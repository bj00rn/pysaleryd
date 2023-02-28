"""
    Dummy conftest.py for pysaleryd.
"""
import asyncio

import aiohttp
import pytest
import pytest_asyncio
from aiohttp import web

@pytest.fixture(scope="session")
def event_loop():
    """Overrides pytest default function scoped event loop"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def server():
    """Websocket test server"""
    async def websocket_handler(request):

        ws = web.WebSocketResponse()
        await ws.prepare(request)

        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                while True:
                    await ws.send_str("#MF: 1+ 0+ 2+\r")
                    await asyncio.sleep(0.5)
        return ws

    app = web.Application()
    app.add_routes([web.get('/', websocket_handler)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 3001)
    await site.start()
    return site




