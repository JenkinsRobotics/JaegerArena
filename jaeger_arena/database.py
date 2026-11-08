"""SQLite v1 schema. Every mutation uses one serialized transaction, including awards."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3

SCHEMA = '''
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS users (
 id TEXT PRIMARY KEY, handle TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS participants (
 id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES users(id), handle TEXT NOT NULL UNIQUE,
 kind TEXT NOT NULL CHECK(kind IN ('human','agent')), display_name TEXT NOT NULL,
 bio TEXT NOT NULL DEFAULT '', public INTEGER NOT NULL DEFAULT 0,
 avatar_profile_id TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS credentials (
 id TEXT PRIMARY KEY, digest TEXT NOT NULL UNIQUE, kind TEXT NOT NULL,
 owner_id TEXT REFERENCES users(id), participant_id TEXT REFERENCES participants(id),
 label TEXT NOT NULL, access TEXT NOT NULL, challenge_id TEXT,
 created_at TEXT NOT NULL, expires_at_s REAL NOT NULL, revoked INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS sessions (
 id TEXT PRIMARY KEY, participant_id TEXT NOT NULL REFERENCES participants(id),
 challenge_id TEXT NOT NULL, challenge_version TEXT NOT NULL, rubric_version TEXT NOT NULL,
 request_id TEXT NOT NULL, input_hash TEXT NOT NULL, configuration TEXT NOT NULL,
 configuration_hash TEXT NOT NULL, skill_id TEXT,
 status TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 0, state TEXT NOT NULL,
 started_at TEXT NOT NULL, started_at_s REAL NOT NULL, finished_at TEXT,
 UNIQUE(participant_id, request_id)
);
CREATE TABLE IF NOT EXISTS events (
 id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id),
 revision INTEGER NOT NULL, request_id TEXT NOT NULL, input_hash TEXT NOT NULL,
 action TEXT NOT NULL, payload TEXT NOT NULL, actor_id TEXT NOT NULL,
 created_at TEXT NOT NULL, response TEXT NOT NULL,
 UNIQUE(session_id,request_id), UNIQUE(session_id,revision)
);
CREATE TABLE IF NOT EXISTS reviews (
 session_id TEXT PRIMARY KEY REFERENCES sessions(id), evaluator_id TEXT NOT NULL,
 request_id TEXT NOT NULL, input_hash TEXT NOT NULL, score_ratio REAL NOT NULL CHECK(score_ratio BETWEEN 0 AND 1),
 feedback TEXT NOT NULL, evidence_reference TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS awards (
 id TEXT PRIMARY KEY, participant_id TEXT NOT NULL REFERENCES participants(id),
 session_id TEXT NOT NULL REFERENCES sessions(id), award_key TEXT NOT NULL,
 xp_points INTEGER NOT NULL CHECK(xp_points>=0), reason TEXT NOT NULL,
 created_at TEXT NOT NULL, UNIQUE(participant_id,award_key)
);
CREATE TABLE IF NOT EXISTS audit (
 id INTEGER PRIMARY KEY AUTOINCREMENT, actor_id TEXT NOT NULL, action TEXT NOT NULL,
 target_id TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_participant ON sessions(participant_id,started_at);
CREATE INDEX IF NOT EXISTS community_public ON participants(public,handle);
'''


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        try:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)')
            versions = [r[0] for r in db.execute('SELECT version FROM schema_version')]
            if versions and versions != [1]:
                raise RuntimeError('Unsupported Arena database schema; use a compatible release')
            db.executescript(SCHEMA)
            if not versions:
                db.execute('INSERT INTO schema_version VALUES (1)')
        finally:
            db.close()
        self.path.chmod(0o600)

    @contextmanager
    def connect(self, write=False):
        db = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA busy_timeout=15000')
        try:
            db.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()
