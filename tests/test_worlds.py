"""World discovery cannot install an adapter, award progress, or unlock hardware."""
from jaeger_arena.catalog import SKILLS
from jaeger_arena.challenges import ADAPTERS
from jaeger_arena.worlds import list_worlds
from conftest import register


def test_catalog_references_and_availability_match_installed_adapters(client):
    catalog = client.get('/api/worlds').json()
    assert catalog['schema_version'] == 'arena.world_catalog/v1'
    assert catalog['progression_status'] == 'planned'
    worlds = catalog['worlds']
    assert len({w['id'] for w in worlds}) == len(worlds)
    published = client.get('/api/challenges').json()['challenges']
    grouped = [c for w in worlds for c in w['challenges']]
    assert sorted(c['id'] for c in grouped) == sorted(c['id'] for c in published)
    assert {c['id']: c for c in grouped} == {c['id']: c for c in published}
    for world in worlds:
        assert all(SKILLS[d]['kind'] == 'domain' for d in world['domain_ids'])
        assert world['available_challenges_count'] == sum(c['id'] in ADAPTERS for c in world['challenges'])
        assert not world['boss_preview'] or world['boss_preview']['status'] == 'planned'
        for challenge in world['challenges']:
            assert challenge['world_id'] == world['id']
            assert challenge['available'] == (challenge['id'] in ADAPTERS)
            assert all(SKILLS[s]['kind'] == 'skill' for s in challenge['skill_ids'])


def test_planned_world_challenges_cannot_start_or_award_progress(client):
    pid = register(client)
    before = client.get('/api/participants/' + pid).json()
    catalog = client.get('/api/worlds').json()
    for world in catalog['worlds']:
        for c in world['challenges']:
            if c['available']:
                continue
            result = client.post('/api/sessions', json={
                'participant_id': pid, 'challenge_id': c['id'],
                'request_id': 'planned-' + c['id'], 'configuration': {'revision': 'world-test-v1'},
            })
            assert result.status_code == 409
    assert client.get('/api/participants/' + pid + '/sessions').json()['sessions'] == []
    after = client.get('/api/participants/' + pid).json()
    for key in ('xp_points', 'level_index', 'rank', 'skills', 'achievements'):
        assert before[key] == after[key]


def test_world_discovery_does_not_expose_mutable_adapter_definitions():
    catalog = list_worlds()
    commons = next(w for w in catalog['worlds'] if w['id'] == 'commons')
    commons['challenges'][0]['controls'].clear()
    commons['path_preview'].clear()
    fresh = next(w for w in list_worlds()['worlds'] if w['id'] == 'commons')
    assert fresh['challenges'][0]['controls']
    assert fresh['path_preview']
