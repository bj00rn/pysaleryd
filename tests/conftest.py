"""
    Configure testing
"""


import pytest_asyncio

from .utils.test_server import TestServer


@pytest_asyncio.fixture()
async def ws_server():
    """Websocket test server"""
    async with TestServer("localhost", "3001") as server:
        yield server
        await server.close()
