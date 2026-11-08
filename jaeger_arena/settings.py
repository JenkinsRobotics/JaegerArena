from dataclasses import dataclass
import os
from pathlib import Path
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Settings:
    database: Path = Path('.arena/arena.sqlite3')
    public_url: str = 'http://127.0.0.1:8792'
    invite_code: str = ''
    registration_open: bool = True

    def __post_init__(self):
        url = urlsplit(self.public_url)
        if url.scheme not in ('http', 'https') or not url.netloc or url.path not in ('', '/') or url.query or url.fragment or url.username:
            raise ValueError('ARENA_PUBLIC_URL must be an HTTP(S) origin, without a path or credentials')
        if url.scheme != 'https' and url.hostname not in ('localhost', '127.0.0.1', '::1', 'testserver'):
            raise ValueError('Non-local deployments require an HTTPS public URL')

    @property
    def secure_cookie(self):
        return self.public_url.startswith('https:')

    @classmethod
    def from_env(cls):
        return cls(database=Path(os.getenv('ARENA_DATABASE', '.arena/arena.sqlite3')),
                   public_url=os.getenv('ARENA_PUBLIC_URL', 'http://127.0.0.1:8792').rstrip('/'),
                   invite_code=os.getenv('ARENA_INVITE_CODE', ''),
                   registration_open=os.getenv('ARENA_REGISTRATION_OPEN', 'true').lower() == 'true')
