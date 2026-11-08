"""Server-owned controls and transition results; future games implement this boundary."""
from dataclasses import dataclass
from typing import Protocol
from .models import Action, ArenaError


class ChallengeAdapter(Protocol):
    descriptor: dict

    def apply(self, state: dict, command: Action) -> tuple[dict, str, dict | None]: ...


@dataclass
class RecordAdapter:
    descriptor: dict

    def apply(self, state, command):
        state = dict(state)
        if command.action not in ('record_note', 'submit', 'cancel'):
            raise ArenaError(422, 'Unknown control for this challenge')
        if command.action != 'record_note' and command.payload:
            raise ArenaError(422, 'This control takes an empty payload')
        if command.action == 'cancel':
            return state, 'cancelled', None
        if command.action == 'record_note':
            note = command.payload.get('note')
            if set(command.payload) != {'note'} or not isinstance(note, str) or len(note) > 4000 or not note.strip():
                raise ArenaError(422, 'Write an observation before recording it')
            notes = list(state.get('notes', []))
            if len(notes) >= 20:
                raise ArenaError(409, 'This session already has 20 notes; submit or cancel it')
            notes.append(note.strip())
            return {'notes': notes}, 'active', None
        if not state.get('notes'):
            raise ArenaError(409, 'Record an observation before submitting')
        if self.descriptor['id'] == 'connection-check':
            return state, 'completed', {'score_ratio': 1.0,
                'feedback': 'Connection verified: an authenticated participant started a session, recorded an observation, and submitted it. This checks the protocol, not a skill.',
                'evidence_reference': 'server:connection-check/v1'}
        return state, 'awaiting_review', None


COMMON = {'version': '1', 'rubric_version': '1', 'tier': 'practice', 'participant_kinds': ['human', 'agent'],
          'available': True, 'controls': [
              {'action': 'record_note', 'description': 'Record an observation (up to 4,000 characters).',
               'input_schema': {'type': 'object', 'properties': {'note': {'type': 'string', 'minLength': 1, 'maxLength': 4000}}, 'required': ['note'], 'additionalProperties': False}},
              {'action': 'submit', 'description': 'Submit the session after at least one observation.', 'input_schema': {'type': 'object', 'properties': {}, 'additionalProperties': False}},
              {'action': 'cancel', 'description': 'Cancel without an award.', 'input_schema': {'type': 'object', 'properties': {}, 'additionalProperties': False}}]}
ADAPTERS = {
    'connection-check': RecordAdapter({**COMMON, 'id': 'connection-check', 'title': 'Arena connection check',
        'kind': 'protocol', 'description': 'Exercise identity, session controls, logging, and a server-generated review. No game and no mastery claim.',
        'review': 'automatic protocol verification', 'xp_policy': '10 XP once per participant for version 1'}),
    'skill-practice': RecordAdapter({**COMMON, 'id': 'skill-practice', 'title': 'Skill practice record',
        'kind': 'evidence', 'description': 'Choose a skill, record practice evidence, and submit it for an independent operator review.',
        'review': 'trusted evaluator required', 'xp_policy': '10 XP after review, at most once per skill per UTC day'}),
}
PLANNED = [
    {'id': 'tic-tac-toe', 'title': 'Tic-tac-toe', 'kind': 'game', 'tier': 'unranked', 'available': False,
     'description': 'First planned game adapter: turns, legal moves, opponents, and match results. No game is installed yet.'},
    {'id': 'physical-tests', 'title': 'Physical & robotics trials', 'kind': 'physical', 'tier': 'verified', 'available': False,
     'description': 'Planned instrumented trials, units, environment records, and independent verification. No hardware controls are exposed.'},
]


def list_challenges():
    return [a.descriptor for a in ADAPTERS.values()] + PLANNED


def adapter(challenge_id):
    if challenge_id not in ADAPTERS:
        raise ArenaError(409, 'This challenge has no installed adapter yet')
    return ADAPTERS[challenge_id]
