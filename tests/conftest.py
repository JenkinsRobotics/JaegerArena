from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from jaeger_arena.app import create_app
from jaeger_arena.settings import Settings


@pytest.fixture
def app(tmp_path):
    return create_app(Settings(database=tmp_path/'arena.sqlite3', public_url='http://testserver'))


@pytest.fixture
def client(app):
    with TestClient(app, headers={'X-Arena-Client': 'web'}) as client:
        yield client


def register(client, handle='alice'):
    result = client.post('/api/auth/register', json={'handle': handle, 'display_name': handle.title(), 'password': 'A strong test password 123'})
    assert result.status_code == 201, result.text
    return client.get('/api/me').json()['participant_id']


def start(client, pid, *, challenge='connection-check', request_id='start_request_1', skill=None, revision='test-v1'):
    body = {'participant_id': pid, 'challenge_id': challenge, 'request_id': request_id,
            'configuration': {'revision': revision}, 'skill_id': skill}
    result = client.post('/api/sessions', json=body)
    assert result.status_code == 201, result.text
    return result.json()


def act(client, sid, action, revision, request_id, note=''):
    return client.post(f'/api/sessions/{sid}/actions', json={'request_id': request_id, 'expected_revision': revision, 'action': action, 'payload': {'note': note} if action=='record_note' else {}})


def submit(client, session):
    result = act(client, session['id'], 'record_note', 0, 'record_note_1', 'A retained observation with evidence.')
    assert result.status_code == 200, result.text
    result = act(client, session['id'], 'submit', 1, 'submit_request_1')
    assert result.status_code == 200, result.text
    return result.json()
