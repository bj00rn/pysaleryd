import asyncio

import aiohttp
import pytest
import pytest_asyncio

from pysaleryd.client import Client, State

__author__ = "Björn Dalfors"
__copyright__ = "Björn Dalfors"
__license__ = "MIT"


async def on_shutdown(app):
    """Shutdown ws connections on shutdown"""
    for ws in set(app["websockets"]):
        try:
            await ws.close(
                code=aiohttp.WSCloseCode.GOING_AWAY, message="Server shutdown"
            )
        except Exception:
            pass


@pytest_asyncio.fixture
async def hrv_client(ws_server):
    """HRV Client"""
    try:
        async with aiohttp.ClientSession() as session:
            async with Client("localhost", 3001, session) as client:
                yield client
    except Exception:
        pass


@pytest.mark.asyncio
async def test_client_connect(hrv_client: Client):
    """test connect"""
    assert hrv_client.state == State.RUNNING


@pytest.mark.asyncio
async def test_client_connect_unsresponsive():
    """test status when client is unresponsive"""
    async with aiohttp.ClientSession() as session:
        client = Client("localhost", 3002, session)
        try:
            await client.connect()
        except Exception:  # noqa: W0718
            pass

        assert client.state == State.STOPPED


@pytest.mark.asyncio
async def test_handler(hrv_client: Client, mocker):
    """Test handler callback"""
    handler = mocker.Mock()

    def broken_handler(data):
        raise Exception()

    hrv_client.add_handler(broken_handler)
    hrv_client.add_handler(handler)
    await asyncio.sleep(3)
    handler.assert_called()


@pytest.mark.asyncio
async def test_get_data(hrv_client: Client, mocker):
    """Test get data"""
    await asyncio.sleep(1)
    assert isinstance(hrv_client.data, dict)
    assert any(hrv_client.data.keys())


@pytest.mark.asyncio
async def test_reconnect(hrv_client: Client, ws_server):
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
async def test_send_command(hrv_client: Client, mocker):
    """Test send command"""
    await hrv_client.send_command("MF", "0")


@pytest.mark.asyncio
async def test_disconnect(hrv_client: Client, mocker):
    """Test send command"""
    hrv_client.disconnect()
    await asyncio.sleep(2)
    assert hrv_client.state == State.STOPPED
    await asyncio.sleep(2)
    assert hrv_client._socket._ws.closed
