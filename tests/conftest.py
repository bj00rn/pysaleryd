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


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async def cleanup():
        await ws.close(code=aiohttp.WSCloseCode.GOING_AWAY, message="Server shutdown")

    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                while True:
                    await ws.send_str("#MF: 1+ 0+ 2+1\r")
                    await asyncio.sleep(0.5)
    finally:
        await asyncio.shield(cleanup())

    return ws


@pytest_asyncio.fixture()
async def ws_server(aiohttp_server: web.Server):
    """Websocket test server"""
    app = web.Application()

    app.add_routes([web.get("/", websocket_handler)])
    return await aiohttp_server(app, port=3001)
