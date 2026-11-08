from contextlib import closing
import time
from fastapi.testclient import TestClient
from jaeger_arena.app import create_app
from jaeger_arena.settings import Settings
from conftest import register, start, submit


def test_account_session_and_logout(client):
    pid = register(client)
    cookie = client.cookies.get('arena_session')
    assert cookie
    profile = client.get('/api/participants/'+pid).json()
    assert profile['kind'] == 'human' and profile['level_index'] == 1
    assert profile['rank'] == 'Unranked' and profile['skills'] == []
    assert client.post('/api/auth/logout').status_code == 200
    assert client.get('/api/me').status_code == 401
    assert client.get('/api/me', headers={'Authorization':'Bearer '+cookie}).status_code == 401
    assert client.post('/api/auth/login', json={'handle':'alice','password':'wrong'}).status_code == 401
    assert client.post('/api/auth/login', json={'handle':'alice','password':'A strong test password 123'}).status_code == 200


def test_private_profile_and_log_isolation(client, app):
    alice = register(client)
    session = start(client, alice)
    with closing(TestClient(app, headers={'X-Arena-Client':'web'})) as bob:
        register(bob, 'bob')
        assert bob.get('/api/participants/'+alice).status_code == 404
        assert bob.get('/api/sessions/'+session['id']).status_code == 404
        assert bob.get('/api/participants/'+alice+'/tokens').status_code == 404
        assert bob.patch('/api/participants/'+alice,json={'display_name':'Hijack','public':True}).status_code == 404
        assert bob.get('/api/community').json()['total_count'] == 0
    assert client.patch('/api/participants/'+alice,json={'display_name':'Alice','public':True}).status_code == 200
    with closing(TestClient(app)) as public:
        profile = public.get('/api/participants/'+alice).json()
        assert 'owner_id' not in profile and 'password_hash' not in profile
        assert public.get('/api/community').json()['total_count'] == 1
        assert public.get('/api/sessions/'+session['id']).status_code == 401


def test_agent_credentials_are_bound_and_revocable(client, app):
    human = register(client)
    agent = client.post('/api/agents',json={'handle':'mochi_agent','display_name':'Mochi'}).json()['id']
    result = client.post('/api/participants/'+agent+'/tokens',json={'label':'MCP','access':'play'}).json()
    with closing(TestClient(app,headers={'Authorization':'Bearer '+result['token']})) as machine:
        assert machine.get('/api/me').json()['participant_id'] == agent
        assert len(machine.get('/api/me').json()['participants']) == 1
        assert machine.get('/api/participants/'+human).status_code == 404
        assert machine.post('/api/agents',json={'handle':'rogue_agent','display_name':'Rogue'}).status_code == 403
        assert machine.post('/api/participants/'+agent+'/tokens',json={}).status_code == 403
        body={'participant_id':human,'challenge_id':'connection-check','request_id':'steal_request_1','configuration':{'revision':'v1'}}
        assert machine.post('/api/sessions',json=body).status_code == 404
        session=start(machine,agent)
        assert submit(machine,session)['status']=='completed'
        assert client.delete('/api/tokens/'+result['id']).status_code == 200
        assert machine.get('/api/me').status_code == 401
    records = client.get('/api/participants/'+agent+'/tokens').json()['credentials']
    assert 'token' not in records[0] and 'digest' not in records[0]
    with app.state.arena.db.connect() as db:
        row=db.execute('SELECT * FROM credentials WHERE id=?',(result['id'],)).fetchone()
        assert result['token'] not in str(dict(row))


def test_readonly_and_expired_keys(client, app):
    pid=register(client)
    key=client.post('/api/participants/'+pid+'/tokens',json={'access':'read'}).json()
    with closing(TestClient(app,headers={'Authorization':'Bearer '+key['token']})) as machine:
        assert machine.get('/api/me').status_code == 200
        result=machine.post('/api/sessions',json={'participant_id':pid,'challenge_id':'connection-check','request_id':'readonly_request','configuration':{'revision':'v1'}})
        assert result.status_code == 403
        with app.state.arena.db.connect(write=True) as db:
            db.execute('UPDATE credentials SET expires_at_s=? WHERE id=?',(time.time()-1,key['id']))
        assert machine.get('/api/me').status_code == 401


def test_character_traits_do_not_grant_progress(client):
    pid=register(client)
    result=client.patch('/api/participants/'+pid,json={'display_name':'Alice','avatar_profile_id':'robotics_architect:jaeger_ai'})
    assert result.status_code == 200
    p=result.json()
    assert p['avatar']['traits']['domains']['technology'] > 0
    assert p['xp_points']==0 and p['skills']==[] and p['rank']=='Unranked'
    assert client.patch('/api/participants/'+pid,json={'display_name':'Alice','avatar_profile_id':'../../secret'}).status_code==422


def test_registration_controls_and_cookie_flags(tmp_path):
    app=create_app(Settings(database=tmp_path/'invite.db',public_url='https://arena.example',invite_code='invite123'))
    with TestClient(app,base_url='https://arena.example',headers={'X-Arena-Client':'web'}) as client:
        body={'handle':'alice','display_name':'Alice','password':'A strong password 123'}
        assert client.post('/api/auth/register',json=body).status_code==403
        result=client.post('/api/auth/register',json={**body,'invite_code':'invite123'})
        cookie=result.headers['set-cookie'].lower()
        assert 'secure' in cookie and 'httponly' in cookie and 'samesite=strict' in cookie


def test_origins_hosts_size_and_validation(client):
    body={'handle':'alice','display_name':'Alice','password':'sensitive'}
    bad=client.post('/api/auth/register',json=body)
    assert bad.status_code==422 and 'sensitive' not in bad.text
    assert client.post('/api/auth/register',json=body,headers={'Origin':'https://evil.example'}).status_code==403
    assert client.get('/api/health',headers={'Host':'evil.example'}).status_code==400
    assert client.post('/api/auth/register',content='x'*65537).status_code==413
    client.headers.pop('X-Arena-Client')
    assert client.post('/api/auth/login',json={'handle':'alice','password':'wrong'}).status_code==403
    assert client.post('/mcp/',json={}).status_code==401
