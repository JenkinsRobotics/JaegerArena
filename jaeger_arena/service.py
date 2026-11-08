"""Shared business rules for REST and MCP. No renderer or agent-runtime imports."""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import secrets
import sqlite3
import time
import uuid
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from .catalog import AVATAR_PROFILES, CATALOG, SKILLS
from .challenges import adapter
from .database import Database
from .models import ArenaError, Action, AgentCreate, ProfileUpdate, Register, Review, StartSession, TokenCreate


def now():
    return datetime.now(timezone.utc).isoformat()


def uid(prefix):
    return prefix + '_' + uuid.uuid4().hex


def dump(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass(frozen=True)
class Principal:
    credential_id: str
    kind: str
    owner_id: str | None
    participant_id: str | None
    access: str
    challenge_id: str | None = None


class Arena:
    def __init__(self, settings):
        self.settings = settings
        self.db = Database(settings.database)
        self.passwords = PasswordHasher()
        self.dummy_hash = self.passwords.hash(secrets.token_urlsafe(32))

    def audit(self, db, actor, action, target):
        db.execute('INSERT INTO audit(actor_id,action,target_id,created_at) VALUES(?,?,?,?)', (actor, action, target, now()))

    def issue(self, db, *, kind, owner_id, participant_id, access, label, duration_s, challenge_id=None):
        token = 'arena_' + secrets.token_urlsafe(40)
        key_id = uid('key')
        expires = time.time() + duration_s
        db.execute('INSERT INTO credentials VALUES(?,?,?,?,?,?,?,?,?,?,0)',
                   (key_id, digest(token), kind, owner_id, participant_id, label, access, challenge_id, now(), expires))
        return {'id': key_id, 'token': token, 'expires_at_s': expires, 'access': access}

    def authenticate(self, token, *, mcp=False):
        if not token or len(token) > 300:
            raise ArenaError(401, 'Authentication required')
        with self.db.connect() as db:
            row = db.execute('SELECT * FROM credentials WHERE digest=? AND revoked=0 AND expires_at_s>?',
                             (digest(token), time.time())).fetchone()
        if not row or (mcp and row['kind'] != 'participant'):
            raise ArenaError(401, 'Credential is invalid, expired, revoked, or unsuitable for this transport')
        return Principal(row['id'], row['kind'], row['owner_id'], row['participant_id'], row['access'], row['challenge_id'])

    def owner(self, principal):
        if principal.kind != 'session':
            raise ArenaError(403, 'A human account session is required')

    def owned(self, db, principal, participant_id, *, write=False):
        if principal.kind == 'evaluator' or (write and principal.access != 'play'):
            raise ArenaError(403, 'This credential cannot perform that action')
        row = db.execute('SELECT * FROM participants WHERE id=?', (participant_id,)).fetchone()
        allowed = row and (row['owner_id'] == principal.owner_id if principal.kind == 'session' else row['id'] == principal.participant_id)
        if not allowed:
            raise ArenaError(404, 'Participant not found')
        return row

    def register(self, data: Register):
        if not self.settings.registration_open:
            raise ArenaError(403, 'Registration is closed on this server')
        if self.settings.invite_code and not secrets.compare_digest(self.settings.invite_code, data.invite_code):
            raise ArenaError(403, 'A valid invitation code is required')
        password_hash = self.passwords.hash(data.password)
        user_id, participant_id = uid('usr'), uid('p')
        try:
            with self.db.connect(write=True) as db:
                db.execute('INSERT INTO users VALUES(?,?,?,?)', (user_id, data.handle, password_hash, now()))
                db.execute('INSERT INTO participants(id,owner_id,handle,kind,display_name,created_at) VALUES(?,?,?,?,?,?)',
                           (participant_id, user_id, data.handle, 'human', data.display_name, now()))
                self.audit(db, user_id, 'account.created', participant_id)
                return self.issue(db, kind='session', owner_id=user_id, participant_id=participant_id, access='play', label='Browser session', duration_s=86400)
        except sqlite3.IntegrityError:
            raise ArenaError(409, 'That handle is unavailable') from None

    def login(self, handle, password):
        with self.db.connect() as db:
            row = db.execute('SELECT * FROM users WHERE handle=?', (handle,)).fetchone()
        try:
            self.passwords.verify(row['password_hash'] if row else self.dummy_hash, password)
        except VerificationError:
            raise ArenaError(401, 'Incorrect handle or password') from None
        if not row:
            raise ArenaError(401, 'Incorrect handle or password')
        with self.db.connect(write=True) as db:
            p = db.execute("SELECT id FROM participants WHERE owner_id=? AND kind='human'", (row['id'],)).fetchone()
            return self.issue(db, kind='session', owner_id=row['id'], participant_id=p['id'], access='play', label='Browser session', duration_s=86400)

    def logout(self, principal):
        with self.db.connect(write=True) as db:
            db.execute('UPDATE credentials SET revoked=1 WHERE id=?', (principal.credential_id,))

    def me(self, principal):
        if principal.kind == 'evaluator':
            raise ArenaError(403, 'Evaluator credentials are only for reviews')
        with self.db.connect() as db:
            if principal.kind == 'session':
                rows = db.execute('SELECT * FROM participants WHERE owner_id=? ORDER BY created_at', (principal.owner_id,)).fetchall()
            else:
                rows = db.execute('SELECT * FROM participants WHERE id=?', (principal.participant_id,)).fetchall()
            return {'credential_kind': principal.kind, 'access': principal.access, 'participant_id': principal.participant_id,
                    'participants': [self.profile(db, row, detail=False) for row in rows]}

    def create_agent(self, principal, data: AgentCreate):
        self.owner(principal)
        participant_id = uid('p')
        try:
            with self.db.connect(write=True) as db:
                if db.execute('SELECT COUNT(*) FROM participants WHERE owner_id=?', (principal.owner_id,)).fetchone()[0] >= 25:
                    raise ArenaError(409, 'This account has reached its participant limit')
                db.execute('INSERT INTO participants(id,owner_id,handle,kind,display_name,created_at) VALUES(?,?,?,?,?,?)',
                           (participant_id, principal.owner_id, data.handle, 'agent', data.display_name, now()))
                self.audit(db, principal.credential_id, 'agent.created', participant_id)
                row = db.execute('SELECT * FROM participants WHERE id=?', (participant_id,)).fetchone()
                return self.profile(db, row)
        except sqlite3.IntegrityError:
            raise ArenaError(409, 'That handle is unavailable') from None

    def update_profile(self, principal, participant_id, data: ProfileUpdate):
        self.owner(principal)
        if data.avatar_profile_id and data.avatar_profile_id not in AVATAR_PROFILES:
            raise ArenaError(422, 'Unknown avatar profile reference')
        with self.db.connect(write=True) as db:
            self.owned(db, principal, participant_id, write=True)
            db.execute('UPDATE participants SET display_name=?,bio=?,public=?,avatar_profile_id=? WHERE id=?',
                       (data.display_name, data.bio, int(data.public), data.avatar_profile_id, participant_id))
            self.audit(db, principal.credential_id, 'profile.updated', participant_id)
            return self.profile(db, db.execute('SELECT * FROM participants WHERE id=?', (participant_id,)).fetchone())

    def create_token(self, principal, participant_id, data: TokenCreate):
        self.owner(principal)
        with self.db.connect(write=True) as db:
            self.owned(db, principal, participant_id)
            count = db.execute("SELECT COUNT(*) FROM credentials WHERE participant_id=? AND kind='participant' AND revoked=0 AND expires_at_s>?", (participant_id, time.time())).fetchone()[0]
            if count >= 10:
                raise ArenaError(409, 'Revoke an existing key before creating another')
            result = self.issue(db, kind='participant', owner_id=principal.owner_id, participant_id=participant_id,
                                access=data.access, label=data.label, duration_s=data.expires_in_days*86400)
            self.audit(db, principal.credential_id, 'credential.created', result['id'])
            return result

    def tokens(self, principal, participant_id):
        self.owner(principal)
        with self.db.connect() as db:
            self.owned(db, principal, participant_id)
            return [dict(r) for r in db.execute("SELECT id,label,access,created_at,expires_at_s,revoked FROM credentials WHERE participant_id=? AND kind='participant' ORDER BY created_at DESC", (participant_id,))]

    def revoke(self, principal, token_id):
        self.owner(principal)
        with self.db.connect(write=True) as db:
            row = db.execute("SELECT * FROM credentials WHERE id=? AND owner_id=? AND kind='participant'", (token_id, principal.owner_id)).fetchone()
            if not row:
                raise ArenaError(404, 'Credential not found')
            db.execute('UPDATE credentials SET revoked=1 WHERE id=?', (token_id,))
            self.audit(db, principal.credential_id, 'credential.revoked', token_id)

    def evaluator_key(self, challenge_id, label, expires_in_days=7):
        # Operator-only CLI; deliberately not exposed through REST or MCP.
        if challenge_id != 'skill-practice':
            raise ArenaError(422, 'Only skill-practice accepts external reviews')
        with self.db.connect(write=True) as db:
            result = self.issue(db, kind='evaluator', owner_id=None, participant_id=None, access='review', label=label,
                                challenge_id=challenge_id, duration_s=expires_in_days*86400)
            self.audit(db, 'operator-cli', 'evaluator.created', result['id'])
            return result

    def profile(self, db, row, *, detail=True):
        xp = db.execute('SELECT COALESCE(SUM(xp_points),0) FROM awards WHERE participant_id=?', (row['id'],)).fetchone()[0]
        counts = {r['status']: r['n'] for r in db.execute('SELECT status,COUNT(*) AS n FROM sessions WHERE participant_id=? GROUP BY status', (row['id'],))}
        result = {k: row[k] for k in ('id', 'handle', 'display_name', 'bio', 'kind', 'created_at', 'avatar_profile_id')}
        result.update(public=bool(row['public']), xp_points=xp, level_index=1+xp//100, level_progress_ratio=(xp%100)/100,
                      next_level_xp_points=(1+xp//100)*100, rank='Unranked', ranked_matches_count=0,
                      completed_sessions_count=counts.get('completed', 0), awaiting_review_count=counts.get('awaiting_review', 0))
        avatar = AVATAR_PROFILES.get(row['avatar_profile_id'])
        result['avatar'] = avatar
        if detail:
            result['skills'] = self.skill_evidence(db, row['id'])
            result['achievements'] = [dict(r) for r in db.execute("SELECT reason,created_at FROM awards WHERE participant_id=? AND award_key='connection-check:1'", (row['id'],))]
        return result

    def skill_evidence(self, db, participant_id):
        rows = db.execute('''SELECT s.skill_id,s.configuration_hash,s.challenge_id,s.challenge_version,s.rubric_version,
                            r.score_ratio,r.created_at,s.id AS session_id FROM reviews r JOIN sessions s ON s.id=r.session_id
                            WHERE s.participant_id=? AND s.skill_id IS NOT NULL ORDER BY r.created_at DESC''', (participant_id,)).fetchall()
        latest = {}
        for row in rows:
            key = (row['skill_id'], row['configuration_hash'], row['challenge_id'], row['challenge_version'], row['rubric_version'])
            if key not in latest:
                latest[key] = {**dict(row), 'reviewed_attempts_count': 0}
            latest[key]['reviewed_attempts_count'] += 1
        # Separate configurations/rubrics stay separate; no invented universal mastery score.
        return list(latest.values())

    def get_profile(self, participant_id, principal=None):
        with self.db.connect() as db:
            row = db.execute('SELECT * FROM participants WHERE id=?', (participant_id,)).fetchone()
            if not row:
                raise ArenaError(404, 'Participant not found')
            if not row['public']:
                if principal is None:
                    raise ArenaError(404, 'Participant not found')
                self.owned(db, principal, participant_id)
            return self.profile(db, row)

    def community(self, query='', kind='', limit=24, offset=0):
        query = query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        where = "public=1 AND (handle LIKE ? ESCAPE '\\' OR display_name LIKE ? ESCAPE '\\')"
        args = ['%'+query+'%', '%'+query+'%']
        if kind:
            where += ' AND kind=?'
            args.append(kind)
        with self.db.connect() as db:
            total = db.execute('SELECT COUNT(*) FROM participants WHERE '+where, args).fetchone()[0]
            rows = db.execute('SELECT * FROM participants WHERE '+where+' ORDER BY handle LIMIT ? OFFSET ?', [*args, limit, offset]).fetchall()
            return {'participants': [self.profile(db, row, detail=False) for row in rows], 'total_count': total, 'offset_count': offset}

    def _session(self, db, row):
        result = {k: row[k] for k in ('id', 'participant_id', 'challenge_id', 'challenge_version', 'rubric_version', 'status', 'revision', 'skill_id', 'started_at', 'finished_at', 'configuration_hash')}
        result['configuration'] = json.loads(row['configuration'])
        result['state'] = json.loads(row['state'])
        result['controls'] = adapter(row['challenge_id']).descriptor['controls'] if row['status'] == 'active' else ([{'action': 'cancel', 'description': 'Withdraw this submission.'}] if row['status'] == 'awaiting_review' else [])
        review = db.execute('SELECT score_ratio,feedback,evidence_reference,created_at FROM reviews WHERE session_id=?', (row['id'],)).fetchone()
        result['review'] = dict(review) if review else None
        result['xp_awarded_points'] = db.execute('SELECT COALESCE(SUM(xp_points),0) FROM awards WHERE session_id=?', (row['id'],)).fetchone()[0]
        result['events'] = [{**dict(r), 'payload': json.loads(r['payload'])} for r in db.execute('SELECT revision,action,payload,created_at FROM events WHERE session_id=? ORDER BY revision', (row['id'],))]
        stop = next((e['created_at'] for e in result['events'] if e['action'] in ('submit', 'cancel')), None)
        end_s = datetime.fromisoformat(stop).timestamp() if stop else time.time()
        result['metrics'] = {'interaction_duration_s': round(max(0, end_s-row['started_at_s']), 3),
                             'actions_count': len(result['events'])}
        return result

    def session(self, principal, session_id):
        with self.db.connect() as db:
            row = db.execute('SELECT * FROM sessions WHERE id=?', (session_id,)).fetchone()
            if not row:
                raise ArenaError(404, 'Session not found')
            self.owned(db, principal, row['participant_id'])
            return self._session(db, row)

    def start(self, principal, data: StartSession):
        challenge = adapter(data.challenge_id)
        if data.challenge_id == 'skill-practice' and (data.skill_id not in SKILLS or SKILLS[data.skill_id]['kind'] != 'skill'):
            raise ArenaError(422, 'Choose a skill leaf for this practice record')
        if data.challenge_id == 'connection-check' and data.skill_id is not None:
            raise ArenaError(422, 'The connection check cannot award skill evidence')
        input_hash = digest(dump(data.model_dump()))
        with self.db.connect(write=True) as db:
            self.owned(db, principal, data.participant_id, write=True)
            prior = db.execute('SELECT * FROM sessions WHERE participant_id=? AND request_id=?', (data.participant_id, data.request_id)).fetchone()
            if prior:
                if prior['input_hash'] != input_hash:
                    raise ArenaError(409, 'Request ID was already used with different input')
                return self._session(db, prior)
            if db.execute("SELECT COUNT(*) FROM sessions WHERE participant_id=? AND status IN ('active','awaiting_review')", (data.participant_id,)).fetchone()[0] >= 20:
                raise ArenaError(409, 'Finish or cancel a pending session first (limit 20)')
            sid = uid('s')
            config = dump(data.configuration.model_dump())
            db.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                       (sid, data.participant_id, data.challenge_id, challenge.descriptor['version'], challenge.descriptor['rubric_version'],
                        data.request_id, input_hash, config, digest(config), data.skill_id, 'active', 0, dump({'notes': []}), now(), time.time(), None))
            self.audit(db, principal.credential_id, 'session.started', sid)
            return self._session(db, db.execute('SELECT * FROM sessions WHERE id=?', (sid,)).fetchone())

    def award(self, db, row, key, reason):
        db.execute('INSERT OR IGNORE INTO awards VALUES(?,?,?,?,?,?,?)',
                   (uid('xp'), row['participant_id'], row['id'], key, 10, reason, now()))

    def act(self, principal, session_id, command: Action):
        command_hash = digest(dump(command.model_dump()))
        with self.db.connect(write=True) as db:
            row = db.execute('SELECT * FROM sessions WHERE id=?', (session_id,)).fetchone()
            if not row:
                raise ArenaError(404, 'Session not found')
            self.owned(db, principal, row['participant_id'], write=True)
            prior = db.execute('SELECT * FROM events WHERE session_id=? AND request_id=?', (session_id, command.request_id)).fetchone()
            if prior:
                if prior['input_hash'] != command_hash:
                    raise ArenaError(409, 'Request ID was already used with different input')
                return json.loads(prior['response'])
            if row['revision'] != command.expected_revision:
                raise ArenaError(409, 'Session revision changed; fetch current state before acting')
            if row['status'] != 'active' and not (row['status'] == 'awaiting_review' and command.action == 'cancel'):
                raise ArenaError(409, 'This session does not accept that control now')
            state, status, review = adapter(row['challenge_id']).apply(json.loads(row['state']), command)
            finished = now() if status in ('completed', 'cancelled') else None
            db.execute('UPDATE sessions SET state=?,status=?,revision=revision+1,finished_at=? WHERE id=?', (dump(state), status, finished, session_id))
            db.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?,?)', (uid('evt'), session_id, row['revision']+1, command.request_id,
                       command_hash, command.action, dump(command.payload), principal.credential_id, now(), '{}'))
            if review:
                db.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?,?,?)', (session_id, 'server:connection-check/v1', command.request_id, command_hash,
                           review['score_ratio'], review['feedback'], review['evidence_reference'], now()))
                self.award(db, row, 'connection-check:1', 'Connected to the arena')
            result = self._session(db, db.execute('SELECT * FROM sessions WHERE id=?', (session_id,)).fetchone())
            db.execute('UPDATE events SET response=? WHERE session_id=? AND request_id=?', (dump(result), session_id, command.request_id))
            return result

    def review(self, principal, session_id, data: Review):
        if principal.kind != 'evaluator' or principal.access != 'review':
            raise ArenaError(403, 'Only a scoped evaluator can submit a review')
        input_hash = digest(dump(data.model_dump()))
        with self.db.connect(write=True) as db:
            row = db.execute('SELECT * FROM sessions WHERE id=? AND challenge_id=?', (session_id, principal.challenge_id)).fetchone()
            if not row:
                raise ArenaError(404, 'Session not found for this evaluator')
            prior = db.execute('SELECT * FROM reviews WHERE session_id=?', (session_id,)).fetchone()
            if prior:
                if prior['evaluator_id'] == principal.credential_id and prior['input_hash'] == input_hash:
                    return self._session(db, row)
                raise ArenaError(409, 'This session already has a review')
            if row['status'] != 'awaiting_review':
                raise ArenaError(409, 'Only a submitted session can be reviewed')
            db.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?,?,?)', (session_id, principal.credential_id, data.request_id, input_hash,
                       data.score_ratio, data.feedback, data.evidence_reference, now()))
            db.execute("UPDATE sessions SET status='completed',finished_at=?,revision=revision+1 WHERE id=?", (now(), session_id))
            self.award(db, row, 'practice:'+row['skill_id']+':'+row['started_at'][:10], 'Reviewed practice: '+SKILLS[row['skill_id']]['name'])
            self.audit(db, principal.credential_id, 'session.reviewed', session_id)
            return self._session(db, db.execute('SELECT * FROM sessions WHERE id=?', (session_id,)).fetchone())

    def review_queue(self, principal, limit=25):
        if principal.kind != 'evaluator':
            raise ArenaError(403, 'Evaluator access required')
        with self.db.connect() as db:
            rows = db.execute("SELECT * FROM sessions WHERE challenge_id=? AND status='awaiting_review' ORDER BY started_at LIMIT ?", (principal.challenge_id, limit)).fetchall()
            return [self._session(db, row) for row in rows]

    def history(self, principal, participant_id, limit=25, offset=0):
        with self.db.connect() as db:
            self.owned(db, principal, participant_id)
            rows = db.execute('SELECT * FROM sessions WHERE participant_id=? ORDER BY started_at DESC LIMIT ? OFFSET ?', (participant_id, limit, offset)).fetchall()
            return [self._session(db, row) for row in rows]
