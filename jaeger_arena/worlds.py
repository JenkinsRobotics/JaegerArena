"""Read-only world discovery. Roadmap metadata never grants access or awards."""
import json
from copy import deepcopy
from .catalog import DATA
from .challenges import list_challenges

WORLD_CATALOG = json.loads((DATA / 'worlds.json').read_text())


def list_worlds():
    result = deepcopy(WORLD_CATALOG)
    challenges = list_challenges()
    for world in result['worlds']:
        world['challenges'] = [deepcopy(c) for c in challenges if c['world_id'] == world['id']]
        world['available_challenges_count'] = sum(c['available'] for c in world['challenges'])
    return result
