"""Real network test using the official MCP client, not a JSON-RPC imitation."""
import asyncio
import json
import socket
import threading
import time
import httpx
import uvicorn
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from jaeger_arena.app import create_app
from jaeger_arena.settings import Settings


def test_real_mcp_transport_identity_actions_and_revocation(tmp_path):
    sock=socket.socket()
    sock.bind(('127.0.0.1',0))
    sock.listen()
    port=sock.getsockname()[1]
    origin=f'http://127.0.0.1:{port}'
    app=create_app(Settings(database=tmp_path/'mcp.sqlite3',public_url=origin))
    server=uvicorn.Server(uvicorn.Config(app,log_level='error',lifespan='on'))
    thread=threading.Thread(target=server.run,kwargs={'sockets':[sock]},daemon=True)
    thread.start()
    try:
        for _ in range(100):
            if server.started: break
            time.sleep(.02)
        assert server.started
        with httpx.Client(base_url=origin,headers={'X-Arena-Client':'web'}) as owner:
            assert owner.post('/api/auth/register',json={'handle':'mcp_owner','display_name':'Owner','password':'MCP test password 123'}).status_code==201
            agent=owner.post('/api/agents',json={'handle':'mcp_agent','display_name':'Test agent'}).json()['id']
            key=owner.post('/api/participants/'+agent+'/tokens',json={'access':'play'}).json()
            assert httpx.post(origin+'/mcp/',json={}).status_code==401
            assert httpx.post(origin+'/mcp/',json={},headers={'Authorization':'Bearer '+key['token'],'Origin':'https://evil.example'}).status_code==403

            async def run():
                async with httpx.AsyncClient(headers={'Authorization':'Bearer '+key['token']}) as http:
                    async with streamable_http_client(origin+'/mcp/',http_client=http) as (read,write,_):
                        async with ClientSession(read,write) as client:
                            await client.initialize()
                            tools=await client.list_tools()
                            assert len(tools.tools)==7
                            assert not any('review' in t.name or 'score' in t.name for t in tools.tools)
                            async def call(name,args):
                                result=await client.call_tool(name,args)
                                assert not result.isError, result.content
                                return result.structuredContent or json.loads(result.content[0].text)
                            me=await call('arena_me',{})
                            assert me['id']==agent
                            challenges=await call('arena_list_challenges',{})
                            assert not next(c for c in challenges['challenges'] if c['id']=='tic-tac-toe')['available']
                            s=await call('arena_start_session',{'challenge_id':'connection-check','request_id':'mcp_start_request','configuration':{'revision':'mcp-config-v1'}})
                            await call('arena_act',{'session_id':s['id'],'action':'record_note','payload':{'note':'I can inspect and operate my own session.'},'request_id':'mcp_note_request','expected_revision':0})
                            result=await call('arena_act',{'session_id':s['id'],'action':'submit','request_id':'mcp_submit_request','expected_revision':1})
                            assert result['status']=='completed' and result['xp_awarded_points']==10
                            repeat=await call('arena_act',{'session_id':s['id'],'action':'submit','request_id':'mcp_submit_request','expected_revision':1})
                            assert repeat==result
                            history=await call('arena_history',{})
                            assert history['sessions'][0]['id']==s['id']
                            foreign=await client.call_tool('arena_session',{'session_id':'not_my_session'})
                            assert foreign.isError
            asyncio.run(run())
            assert owner.delete('/api/tokens/'+key['id']).status_code==200
            assert httpx.post(origin+'/mcp/',json={},headers={'Authorization':'Bearer '+key['token']}).status_code==401
    finally:
        server.should_exit=True
        thread.join(timeout=10)
        sock.close()
        assert not thread.is_alive()
