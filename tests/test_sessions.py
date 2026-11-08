from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
import json
from fastapi.testclient import TestClient
from jaeger_arena.models import Action, ArenaError
from jaeger_arena.service import Arena
from conftest import register, start, act, submit


def test_lifecycle_retry_and_one_time_award(client):
    pid=register(client)
    session=start(client,pid)
    assert start(client,pid)['id']==session['id']
    assert act(client,session['id'],'submit',0,'too_early_submit').status_code==409
    result=submit(client,session)
    retry=act(client,session['id'],'submit',1,'submit_request_1')
    assert retry.status_code==200 and retry.json()==result
    assert act(client,session['id'],'record_note',1,'submit_request_1','Different request').status_code==409
    assert act(client,session['id'],'record_note',2,'late_note_request','Too late').status_code==409
    repeat=submit(client,start(client,pid,request_id='second_session_request'))
    assert repeat['xp_awarded_points']==0
    p=client.get('/api/participants/'+pid).json()
    assert p['xp_points']==10 and p['level_index']==1 and p['skills']==[] and len(p['achievements'])==1


def test_concurrent_actions_apply_once(client,app):
    pid=register(client)
    s=start(client,pid)
    arena=app.state.arena
    p=arena.authenticate(client.cookies.get('arena_session'))
    def send(index):
        try:
            arena.act(p,s['id'],Action(action='record_note',expected_revision=0,request_id=f'parallel_{index}',payload={'note':'A concurrent action'}))
            return 200
        except ArenaError as exc:
            return exc.status
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses=list(pool.map(send,[1,2]))
    assert sorted(statuses)==[200,409]
    current=arena.session(p,s['id'])
    assert current['revision']==1 and len(current['events'])==1


def test_trusted_review_and_configuration_provenance(client,app):
    pid=register(client)
    s=submit(client,start(client,pid,challenge='skill-practice',skill='technology.programming'))
    assert s['status']=='awaiting_review' and s['xp_awarded_points']==0
    review={'request_id':'review_request_1','score_ratio':.8,'feedback':'The supplied evidence meets the practice criteria.','evidence_reference':'operator:review-001'}
    assert client.post('/api/sessions/'+s['id']+'/review',json=review).status_code==403
    key=app.state.arena.evaluator_key('skill-practice','Test evaluator')
    with closing(TestClient(app,headers={'Authorization':'Bearer '+key['token']})) as evaluator:
        assert evaluator.get('/api/me').status_code==403
        assert evaluator.get('/api/review-queue').json()['sessions'][0]['id']==s['id']
        result=evaluator.post('/api/sessions/'+s['id']+'/review',json=review)
        assert result.status_code==200 and result.json()['xp_awarded_points']==10
        assert evaluator.post('/api/sessions/'+s['id']+'/review',json=review).status_code==200
        assert evaluator.post('/api/sessions/'+s['id']+'/review',json={**review,'score_ratio':1}).status_code==409
        second=submit(client,start(client,pid,challenge='skill-practice',skill='technology.programming',request_id='second_practice_session',revision='config-v2'))
        r=evaluator.post('/api/sessions/'+second['id']+'/review',json={**review,'request_id':'review_request_2'})
        assert r.json()['xp_awarded_points']==0  # same skill/day, not another award
    p=client.get('/api/participants/'+pid).json()
    assert len(p['skills'])==2 and len({r['configuration_hash'] for r in p['skills']})==2
    assert p['xp_points']==10 and p['rank']=='Unranked'


def test_cancel_and_no_game_adapter(client):
    pid=register(client)
    s=start(client,pid)
    assert act(client,s['id'],'cancel',0,'cancel_request_1').json()['status']=='cancelled'
    assert act(client,s['id'],'record_note',1,'later_note_1','A note').status_code==409
    response=client.post('/api/sessions',json={'participant_id':pid,'challenge_id':'tic-tac-toe','request_id':'game_request_1','configuration':{'revision':'v1'}})
    assert response.status_code==409
    assert client.get('/api/participants/'+pid).json()['xp_points']==0


def test_persistence_and_foreign_keys(client,app):
    pid=register(client)
    s=submit(client,start(client,pid))
    restored=Arena(app.state.arena.settings)
    p=restored.authenticate(client.cookies.get('arena_session'))
    assert restored.session(p,s['id'])['review']['score_ratio']==1
    assert restored.get_profile(pid,p)['xp_points']==10
    with restored.db.connect() as db:
        assert db.execute('PRAGMA foreign_keys').fetchone()[0]==1
        assert db.execute('SELECT version FROM schema_version').fetchone()[0]==1


def test_nonfinite_review_and_unknown_fields_rejected(client):
    pid=register(client)
    result=client.post('/api/sessions',json={'participant_id':pid,'challenge_id':'connection-check','request_id':'bad_input_request','configuration':{'revision':'v1'},'xp_points':999})
    assert result.status_code==422
    assert client.post('/api/sessions/anything/review',content='{"request_id":"review_123","score_ratio":NaN,"feedback":"Invalid score input","evidence_reference":"test"}').status_code==422
