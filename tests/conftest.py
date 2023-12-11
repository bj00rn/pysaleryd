"""
    Configure testing
"""
import asyncio

import pytest
import pytest_asyncio
from aiohttp import web

from .utils.test_server import WebsocketView


@pytest.fixture(scope="session")
def event_loop():
    """Overrides pytest default function scoped event loop"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def ws_server(aiohttp_server: "web.Server"):
    """Websocket test server"""
    app = web.Application()
    app.add_routes([web.view("/", WebsocketView)])
    return await aiohttp_server(app, port=3001)
