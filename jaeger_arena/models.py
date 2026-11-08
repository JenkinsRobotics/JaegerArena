"""API validation; dimensionless scores use _ratio, counters use _count/_points."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, JsonValue

Handle = Annotated[str, StringConstraints(pattern=r'^[a-z][a-z0-9_]{2,31}$')]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
RequestID = Annotated[str, StringConstraints(pattern=r'^[A-Za-z0-9_-]{8,100}$')]


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class Register(Input):
    handle: Handle
    display_name: Name
    password: str = Field(min_length=12, max_length=128)
    invite_code: str = Field(default='', max_length=200)


class Login(Input):
    handle: Handle
    password: str = Field(min_length=1, max_length=128)


class AgentCreate(Input):
    handle: Handle
    display_name: Name


class ProfileUpdate(Input):
    display_name: Name
    bio: str = Field(default='', max_length=600)
    public: bool = False
    avatar_profile_id: str | None = Field(default=None, max_length=100)


class TokenCreate(Input):
    label: Name = 'Agent access'
    access: Literal['read', 'play'] = 'play'
    expires_in_days: int = Field(default=30, ge=1, le=90)


class Configuration(Input):
    revision: str = Field(min_length=1, max_length=100)
    model: str = Field(default='', max_length=200)
    skill_revision: str = Field(default='', max_length=100)
    tools: list[Annotated[str, StringConstraints(min_length=1, max_length=100)]] = Field(default_factory=list, max_length=50)


class StartSession(Input):
    participant_id: str = Field(min_length=1, max_length=60)
    challenge_id: str = Field(min_length=1, max_length=100)
    request_id: RequestID
    configuration: Configuration
    skill_id: str | None = Field(default=None, max_length=100)


class Action(Input):
    request_id: RequestID
    expected_revision: int = Field(ge=0)
    action: str = Field(pattern=r'^[a-z][a-z0-9_]{0,63}$')
    payload: dict[str, JsonValue] = Field(default_factory=dict, max_length=50)


class Review(Input):
    request_id: RequestID
    score_ratio: float = Field(ge=0, le=1)
    feedback: str = Field(min_length=10, max_length=4000)
    evidence_reference: str = Field(min_length=3, max_length=500)


class ArenaError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(message)
