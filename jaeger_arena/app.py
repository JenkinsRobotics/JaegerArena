from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
import time
from urllib.parse import urlsplit
from fastapi import Depends, FastAPI, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import Headers
from . import __version__
from .catalog import AVATARS, CATALOG
from .challenges import list_challenges
from .worlds import list_worlds
from .mcp_server import build_mcp
from .models import Action, AgentCreate, ArenaError, Login, ProfileUpdate, Register, Review, StartSession, TokenCreate
from .service import Arena
from .settings import Settings

WEB = Path(__file__).parent / 'web'
COOKIE = 'arena_session'


class Boundary:
    """Bounded request bodies, origin/host checks, auth throttling, and MCP auth."""
    def __init__(self, app, arena):
        self.app, self.arena = app, arena
        self.hits = defaultdict(deque)

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = Headers(scope=scope)
        path, method = scope['path'], scope['method']
        origin = self.arena.settings.public_url.rstrip('/')
        async def reject(status, message):
            await JSONResponse({'detail': message}, status_code=status, headers={'Cache-Control': 'no-store'})(scope, receive, send)
        if headers.get('host') != urlsplit(origin).netloc:
            return await reject(400, 'Unrecognized host')
        if headers.get('origin') and headers['origin'] != origin:
            return await reject(403, 'Cross-origin requests are not allowed')
        if path.startswith(('/api/', '/mcp')):
            auth_route = path in ('/api/auth/login', '/api/auth/register')
            client = scope.get('client') or ('unknown', 0)
            key = (client[0], auth_route)
            clock = time.monotonic()
            # One process for this release; an edge limiter is required before public rollout.
            if len(self.hits) >= 2048 and key not in self.hits:
                self.hits = defaultdict(deque, {k: v for k, v in self.hits.items() if v and v[-1] > clock-300})
                if len(self.hits) >= 2048:
                    return await reject(429, 'Server is busy; retry later')
            window, limit = (300, 20) if auth_route else (60, 300)
            queue = self.hits[key]
            while queue and queue[0] <= clock-window:
                queue.popleft()
            if len(queue) >= limit:
                return await reject(429, 'Too many requests; retry later')
            queue.append(clock)
            if method in ('POST', 'PUT', 'PATCH', 'DELETE'):
                if path.startswith('/api/') and not headers.get('authorization') and headers.get('x-arena-client') != 'web':
                    return await reject(403, 'Browser mutations require the Arena request header')
                chunks, size = [], 0
                while True:
                    message = await receive()
                    if message['type'] == 'http.disconnect':
                        return
                    size += len(message.get('body', b''))
                    if size > 65536:
                        return await reject(413, 'Request body exceeds 64 KiB')
                    chunks.append(message.get('body', b''))
                    if not message.get('more_body', False):
                        break
                body = b''.join(chunks)
                consumed = False
                original_receive = receive
                async def replay():
                    nonlocal consumed
                    if not consumed:
                        consumed = True
                        return {'type': 'http.request', 'body': body, 'more_body': False}
                    return await original_receive()
                receive = replay
            if path.startswith('/mcp'):
                auth = headers.get('authorization', '')
                try:
                    self.arena.authenticate(auth[7:] if auth.lower().startswith('bearer ') else '', mcp=True)
                except ArenaError as exc:
                    return await reject(exc.status, exc.message)
        async def secure_send(message):
            if message['type'] == 'http.response.start':
                extra = [(b'x-content-type-options', b'nosniff'), (b'referrer-policy', b'no-referrer'),
                         (b'content-security-policy', b"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")]
                if path.startswith(('/api/', '/mcp')):
                    extra.append((b'cache-control', b'no-store'))
                message['headers'] = list(message.get('headers', [])) + extra
            await send(message)
        await self.app(scope, receive, secure_send)


def create_app(settings=None):
    settings = settings or Settings.from_env()
    arena = Arena(settings)
    mcp = build_mcp(arena)
    mcp_app = mcp.streamable_http_app()

    @asynccontextmanager
    async def lifespan(app):
        async with mcp.session_manager.run():
            yield

    app = FastAPI(title='Jaeger Arena', version=__version__, lifespan=lifespan, docs_url=None, redoc_url=None)
    app.state.arena = arena
    app.add_middleware(Boundary, arena=arena)

    @app.exception_handler(ArenaError)
    async def arena_error(request, exc):
        return JSONResponse({'detail': exc.message}, status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse({'detail': 'Invalid request', 'errors': [{'field': '.'.join(map(str, e['loc'])), 'message': e['msg']} for e in exc.errors()]}, status_code=422)

    def optional_principal(request: Request):
        auth = request.headers.get('authorization', '')
        if auth and not auth.lower().startswith('bearer '):
            raise ArenaError(401, 'Use a Bearer participant credential')
        token = auth[7:] if auth.lower().startswith('bearer ') else request.cookies.get(COOKIE)
        return arena.authenticate(token) if token else None

    def authenticated(request: Request):
        p = optional_principal(request)
        if not p:
            raise ArenaError(401, 'Sign in or provide a participant credential')
        return p

    def set_session(response, result):
        response.set_cookie(COOKIE, result['token'], max_age=86400, httponly=True, samesite='strict', secure=settings.secure_cookie, path='/')
        return {'authenticated': True}

    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'version': __version__, 'runtime': 'foundation', 'mcp_path': '/mcp/',
                'registration_open': settings.registration_open, 'invitation_required': bool(settings.invite_code)}

    @app.get('/api/docs', include_in_schema=False)
    def api_schema():
        return RedirectResponse('/openapi.json')

    @app.post('/api/auth/register', status_code=201)
    def register(data: Register, response: Response):
        return set_session(response, arena.register(data))

    @app.post('/api/auth/login')
    def login(data: Login, response: Response):
        return set_session(response, arena.login(data.handle, data.password))

    @app.post('/api/auth/logout')
    def logout(response: Response, p=Depends(authenticated)):
        arena.logout(p)
        response.delete_cookie(COOKIE, path='/', secure=settings.secure_cookie, httponly=True, samesite='strict')
        return {'signed_out': True}

    @app.get('/api/me')
    def me(p=Depends(authenticated)):
        return arena.me(p)

    @app.get('/api/skills')
    def skills():
        return CATALOG

    @app.get('/api/avatar-profiles')
    def avatars():
        return AVATARS

    @app.get('/api/challenges')
    def challenges():
        return {'challenges': list_challenges()}

    @app.get('/api/worlds')
    def worlds():
        return list_worlds()

    @app.get('/api/community')
    def community(q: str = Query('', max_length=100), kind: str = Query('', pattern='^(human|agent)?$'),
                  limit: int = Query(24, ge=1, le=100), offset: int = Query(0, ge=0, le=10000)):
        return arena.community(q, kind, limit, offset)

    @app.post('/api/agents', status_code=201)
    def create_agent(data: AgentCreate, p=Depends(authenticated)):
        return arena.create_agent(p, data)

    @app.get('/api/participants/{participant_id}')
    def profile(participant_id: str, p=Depends(optional_principal)):
        return arena.get_profile(participant_id, p)

    @app.patch('/api/participants/{participant_id}')
    def update_profile(participant_id: str, data: ProfileUpdate, p=Depends(authenticated)):
        return arena.update_profile(p, participant_id, data)

    @app.post('/api/participants/{participant_id}/tokens', status_code=201)
    def create_token(participant_id: str, data: TokenCreate, p=Depends(authenticated)):
        return arena.create_token(p, participant_id, data)

    @app.get('/api/participants/{participant_id}/tokens')
    def tokens(participant_id: str, p=Depends(authenticated)):
        return {'credentials': arena.tokens(p, participant_id)}

    @app.delete('/api/tokens/{token_id}')
    def revoke(token_id: str, p=Depends(authenticated)):
        arena.revoke(p, token_id)
        return {'revoked': True}

    @app.get('/api/participants/{participant_id}/sessions')
    def history(participant_id: str, limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0, le=10000), p=Depends(authenticated)):
        return {'sessions': arena.history(p, participant_id, limit, offset)}

    @app.post('/api/sessions', status_code=201)
    def start(data: StartSession, p=Depends(authenticated)):
        return arena.start(p, data)

    @app.get('/api/sessions/{session_id}')
    def session(session_id: str, p=Depends(authenticated)):
        return arena.session(p, session_id)

    @app.post('/api/sessions/{session_id}/actions')
    def act(session_id: str, data: Action, p=Depends(authenticated)):
        return arena.act(p, session_id, data)

    @app.get('/api/review-queue')
    def review_queue(p=Depends(authenticated)):
        return {'sessions': arena.review_queue(p)}

    @app.post('/api/sessions/{session_id}/review')
    def review(session_id: str, data: Review, p=Depends(authenticated)):
        return arena.review(p, session_id, data)

    @app.get('/')
    def index():
        return FileResponse(WEB / 'index.html')

    @app.get('/favicon.ico', include_in_schema=False)
    def favicon():
        return FileResponse(WEB / 'arena.svg', media_type='image/svg+xml')

    app.mount('/assets', StaticFiles(directory=WEB), name='assets')
    app.mount('/mcp', mcp_app)
    return app
