"""Client tests"""
import asyncio
import logging
import typing

import pytest
import pytest_asyncio

from pysaleryd.client import Client, ConnectionStateEnum

if typing.TYPE_CHECKING:
    from utils.test_server import TestServer

__author__ = "Björn Dalfors"
__copyright__ = "Björn Dalfors"
__license__ = "MIT"


async def has_state(client: Client, state: ConnectionStateEnum):
    try:
        while client.state != state:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        assert client.state == state


@pytest_asyncio.fixture(name="hrv_client")
async def _hrv_client(ws_server: "TestServer"):
    """HRV Client"""
    async with Client("localhost", 3001, 3) as client:
        yield client
        client.disconnect()


@pytest.mark.asyncio
async def test_client_connect(hrv_client: "Client"):
    """test connect"""
    hrv_client.connect()
    await has_state(hrv_client, ConnectionStateEnum.RUNNING)


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
async def test_get_data(hrv_client: "Client", caplog):
    """Test get data"""
    caplog.set_level(logging.DEBUG)
    await asyncio.sleep(5)
    assert isinstance(hrv_client.data, dict)
    assert any(hrv_client.data.keys())


@pytest.mark.asyncio
async def test_reconnect(hrv_client: "Client", ws_server: "TestServer", caplog):
    """Test reconnect"""
    caplog.set_level(logging.DEBUG)

    await asyncio.wait_for(has_state(hrv_client, ConnectionStateEnum.RUNNING), 15)
    ws_server.stop()
    await asyncio.wait_for(has_state(hrv_client, ConnectionStateEnum.RETRYING), 15)
    await ws_server.start()
    await asyncio.wait_for(has_state(hrv_client, ConnectionStateEnum.RUNNING), 15)


@pytest.mark.asyncio
async def test_connect_unresponsive(ws_server: "TestServer", caplog):
    """Test connection is retried when host is unresponsive"""
    caplog.set_level(logging.INFO)

    ws_server.stop()
    await asyncio.sleep(5)
    client = Client("localhost", 3001, 3, 1)
    client.connect()
    await asyncio.sleep(5)
    await asyncio.wait_for(has_state(client, ConnectionStateEnum.NONE), 15)
    await ws_server.start()
    await asyncio.wait_for(has_state(client, ConnectionStateEnum.RUNNING), 15)
    client.disconnect()


@pytest.mark.asyncio
async def test_send_command(hrv_client: "Client"):
    """Test send command"""
    await hrv_client.send_command("MF", 0)


@pytest.mark.asyncio
async def test_disconnect(hrv_client: "Client", caplog):
    caplog.set_level(logging.INFO)
    """Test disconnected client remains disconnected"""
    hrv_client.disconnect()
    await has_state(hrv_client, ConnectionStateEnum.STOPPED)
