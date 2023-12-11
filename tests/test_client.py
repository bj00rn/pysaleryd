"""Client tests"""
import asyncio
import typing

import aiohttp
import pytest
import pytest_asyncio

from pysaleryd.client import Client, State

if typing.TYPE_CHECKING:
    from aiohttp import web_server

__author__ = "Björn Dalfors"
__copyright__ = "Björn Dalfors"
__license__ = "MIT"


@pytest_asyncio.fixture(name="hrv_client")
async def _hrv_client(ws_server):
    """HRV Client"""
    async with aiohttp.ClientSession() as session:
        async with Client("localhost", 3001, session, 3) as client:
            yield client


@pytest.mark.asyncio
async def test_client_connect(hrv_client: "Client"):
    """test connect"""
    assert hrv_client.state == State.RUNNING


@pytest.mark.asyncio
async def test_handler(hrv_client: "Client", mocker):
    """Test handler callback"""

    data = None  # noqa: F841

    def handler(_data):
        nonlocal data
        data = _data

    def broken_handler(data):
        raise Exception()  # pylint: disable=W0719

    hrv_client.add_handler(broken_handler)
    hrv_client.add_handler(handler)
    await asyncio.sleep(5)

    assert isinstance(data, dict)
    assert any(data.keys())


@pytest.mark.asyncio
async def test_get_data(hrv_client: "Client"):
    """Test get data"""
    await asyncio.sleep(5)
    assert isinstance(hrv_client.data, dict)
    assert any(hrv_client.data.keys())


@pytest.mark.asyncio
async def test_reconnect(hrv_client: "Client", ws_server: "web_server.Server"):
    """Test reconnect"""

    async def has_state(state):
        while hrv_client.state != state:
            await asyncio.sleep(0.1)
        return True

    assert await asyncio.wait_for(has_state(State.RUNNING), 15)
    await ws_server.app.shutdown()
    await ws_server.app.startup()
    assert await asyncio.wait_for(has_state(State.RUNNING), 15)


@pytest.mark.asyncio
async def test_send_command(hrv_client: "Client"):
    """Test send command"""
    await hrv_client.send_command("MF", "0")


@pytest.mark.asyncio
async def test_disconnect(hrv_client: "Client"):
    """Test send command"""
    hrv_client.disconnect()
    await asyncio.sleep(2)
    assert hrv_client.state == State.STOPPED
    await asyncio.sleep(2)
    assert hrv_client._socket._ws.closed  # pylint: disable=all
