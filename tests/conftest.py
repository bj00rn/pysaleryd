"""
    Configure testing
"""
import asyncio

import pytest
import pytest_asyncio

from .utils.test_server import TestServer


@pytest.fixture(scope="session")
def event_loop():
    """Overrides pytest default function scoped event loop"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def ws_server():
    """Websocket test server"""
    async with TestServer("localhost", "3001") as server:
        yield server
        server.stop()
