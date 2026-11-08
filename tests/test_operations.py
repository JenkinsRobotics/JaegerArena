import sqlite3
import pytest
from conftest import register, start, submit
from jaeger_arena.operations import backup_database, reset_password


def test_backup_restores_participants_history_and_awards(client, app, tmp_path):
    participant = register(client)
    submit(client, start(client, participant))
    target = tmp_path / 'snapshot.sqlite3'
    backup_database(app.state.arena.db.path, target)
    assert target.stat().st_mode & 0o777 == 0o600
    with sqlite3.connect(target) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert db.execute('SELECT SUM(xp_points) FROM awards WHERE participant_id=?', (participant,)).fetchone()[0] == 10
        assert db.execute('SELECT COUNT(*) FROM reviews').fetchone()[0] == 1
    before = target.read_bytes()
    with pytest.raises(FileExistsError):
        backup_database(app.state.arena.db.path, target)
    assert target.read_bytes() == before
    with pytest.raises(ValueError):
        backup_database(tmp_path / 'absent.sqlite3', tmp_path / 'missing.sqlite3')
    assert not (tmp_path / 'missing.sqlite3').exists()


def test_recovery_revokes_owner_and_agents_but_preserves_progress(client, app):
    human = register(client)
    agent = client.post('/api/agents', json={'handle': 'agent_test', 'display_name': 'Agent'}).json()['id']
    key = client.post('/api/participants/'+agent+'/tokens', json={}).json()['token']
    submit(client, start(client, human))
    reset_password(app.state.arena, 'alice', 'A replacement password 123')
    assert client.get('/api/me').status_code == 401
    assert client.get('/api/me', headers={'Authorization': 'Bearer '+key}).status_code == 401
    assert client.post('/api/auth/login', json={'handle': 'alice', 'password': 'A strong test password 123'}).status_code == 401
    assert client.post('/api/auth/login', json={'handle': 'alice', 'password': 'A replacement password 123'}).status_code == 200
    assert client.get('/api/participants/'+human).json()['xp_points'] == 10
    assert client.get('/api/participants/'+agent).status_code == 200


def test_login_cannot_issue_old_password_session_during_recovery(client, app, monkeypatch):
    register(client)
    arena = app.state.arena
    verify = arena.passwords.verify
    def racing_verify(self, hash_value, password):
        result = verify(hash_value, password)
        reset_password(arena, 'alice', 'Another replacement password 123')
        return result
    monkeypatch.setattr(type(arena.passwords), 'verify', racing_verify)
    assert client.post('/api/auth/login', json={'handle': 'alice', 'password': 'A strong test password 123'}).status_code == 401


def test_readiness_detects_schema_problem(client, app):
    assert client.get('/api/ready').json()['status'] == 'ready'
    with app.state.arena.db.connect(write=True) as db:
        db.execute('UPDATE schema_version SET version=999')
    response = client.get('/api/ready')
    assert response.status_code == 503 and response.json() == {'status': 'unavailable'}
