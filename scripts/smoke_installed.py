#!/usr/bin/env python3
"""Exercise an installed distribution with a disposable database and real MCP."""
import asyncio
import json
from pathlib import Path
import socket
import tempfile
import threading
import time
import httpx
import uvicorn
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from jaeger_arena import __version__
from jaeger_arena.app import create_app
from jaeger_arena.settings import Settings


def main():
    with tempfile.TemporaryDirectory(prefix='arena-release-') as directory:
        sock = socket.socket()
        sock.bind(('127.0.0.1', 0))
        sock.listen()
        origin = f'http://127.0.0.1:{sock.getsockname()[1]}'
        app = create_app(Settings(database=Path(directory)/'arena.sqlite3', public_url=origin))
        server = uvicorn.Server(uvicorn.Config(app, log_level='critical'))
        thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
        thread.start()
        try:
            for _ in range(200):
                if server.started:
                    break
                time.sleep(.025)
            assert server.started, 'Installed server did not start'
            with httpx.Client(base_url=origin, headers={'X-Arena-Client': 'web'}) as owner:
                assert owner.get('/api/ready').json()['version'] == __version__ == '0.1.0'
                for path in ('/', '/assets/app.js', '/assets/profile-cards.css', '/assets/arena-icon.png'):
                    assert owner.get(path).status_code == 200, path
                assert owner.post('/api/auth/register', json={'handle': 'release_owner', 'display_name': 'Release check', 'password': 'Disposable release check password'}).status_code == 201
                agent = owner.post('/api/agents', json={'handle': 'release_agent', 'display_name': 'Release agent'}).json()['id']
                credential = owner.post(f'/api/participants/{agent}/tokens', json={}).json()
                async def exercise():
                    async with httpx.AsyncClient(headers={'Authorization': 'Bearer '+credential['token']}) as http:
                        async with streamable_http_client(origin+'/mcp/', http_client=http) as (read, write, _):
                            async with ClientSession(read, write) as client:
                                await client.initialize()
                                assert len((await client.list_tools()).tools) == 8
                                async def call(name, args):
                                    result = await client.call_tool(name, args)
                                    assert not result.isError, name
                                    return result.structuredContent or json.loads(result.content[0].text)
                                assert (await call('arena_me', {}))['id'] == agent
                                s = await call('arena_start_session', {'challenge_id': 'connection-check', 'request_id': 'release_start_1', 'configuration': {'revision': 'release-smoke-v1'}})
                                await call('arena_act', {'session_id': s['id'], 'action': 'record_note', 'payload': {'note': 'Installed package connection check.'}, 'request_id': 'release_note_1', 'expected_revision': 0})
                                result = await call('arena_act', {'session_id': s['id'], 'action': 'submit', 'request_id': 'release_submit_1', 'expected_revision': 1})
                                assert result['status'] == 'completed' and result['xp_awarded_points'] == 10
                asyncio.run(exercise())
                assert owner.delete('/api/tokens/'+credential['id']).status_code == 200
                assert owner.get('/api/me', headers={'Authorization': 'Bearer '+credential['token']}).status_code == 401
                assert owner.post('/api/auth/logout', json={}).status_code == 200
                assert owner.get('/api/me').status_code == 401
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            sock.close()
            assert not thread.is_alive()
    print('Installed 0.1.0 passed: signup, agent registration, assets, real MCP session, XP, revocation, logout.')


if __name__ == '__main__':
    main()
