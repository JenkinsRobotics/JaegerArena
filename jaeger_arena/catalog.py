import json
from pathlib import Path

DATA = Path(__file__).parent / 'data'
CATALOG = json.loads((DATA / 'skills.json').read_text())
SKILLS = {row['id']: row for row in CATALOG['skills']}
AVATARS = json.loads((DATA / 'avatar_profiles.json').read_text())
AVATAR_PROFILES = {row['id']: row for row in AVATARS['profiles']}
