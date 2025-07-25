"""Client tests"""

import asyncio
import logging
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from websockets.protocol import State

from pysaleryd.client import Client
from pysaleryd.data import DataKey

if TYPE_CHECKING:
    from tests.utils.test_server import TestServer

__author__ = "Björn Dalfors"
__copyright__ = "Björn Dalfors"
__license__ = "MIT"


async def has_state(client: Client, state: State | None):
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
    client = None
    try:
        async with Client("localhost", 3001, 3, connect_timeout=10) as c:
            client = c
            yield client
    finally:
        if client is not None:
            await client.close()


@pytest.mark.asyncio
async def test_client_connect(hrv_client: "Client"):
    """test connect"""
    await has_state(hrv_client, State.OPEN)


@pytest.mark.asyncio
async def test_handler(hrv_client: "Client", mocker, caplog):
    caplog.set_level(logging.DEBUG)
    """Test handler callback"""

    data = None  # noqa: F841

    def handler(_data):
        nonlocal data
        data = _data

    def broken_handler(data):
        raise Exception()  # pylint: disable=W0719

    hrv_client.add_data_handler(broken_handler)
    hrv_client.add_data_handler(handler)
    await asyncio.sleep(5)

    assert isinstance(data, dict)
    assert any(data.keys())


@pytest.mark.asyncio
async def test_state_change_handler(ws_server: "TestServer", mocker, caplog):
    caplog.set_level(logging.DEBUG)
    """Test state change handler callback"""

    class Foo:
        def handler(self, state: State):
            pass

    foo = Foo()
    spy = mocker.spy(foo, "handler")

    client = Client("localhost", 3001, 3, 1)
    client.add_state_change_handler(foo.handler)
    await client.connect()

    await asyncio.sleep(2)
    spy.assert_called_once_with(State.OPEN)
    await ws_server.close()
    await asyncio.sleep(1)
    spy.assert_called_with(State.CLOSED)
    await ws_server.start()
    await asyncio.sleep(5)
    spy.assert_called_with(State.OPEN)


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

    await asyncio.wait_for(has_state(hrv_client, State.OPEN), 15)
    await ws_server.close()
    await asyncio.wait_for(has_state(hrv_client, State.CLOSED), 15)
    await ws_server.start()
    await asyncio.wait_for(has_state(hrv_client, State.OPEN), 15)


@pytest.mark.asyncio
async def test_connect_unresponsive(ws_server: "TestServer", caplog):
    """Test connection is retried when host is unresponsive"""
    caplog.set_level(logging.INFO)

    await ws_server.close()
    await asyncio.sleep(1)
    client = Client("localhost", 3001, 3, 1)
    with pytest.raises(asyncio.TimeoutError):
        await client.connect()

    # await ws_server.start()
    # await asyncio.wait_for(has_state(client, State.OPEN), 15)


@pytest.mark.asyncio
async def test_send_command(hrv_client: "Client"):
    """Test send command"""
    await hrv_client.send_command(DataKey.MODE_FAN, 0)


@pytest.mark.asyncio
async def test_disconnect(hrv_client: "Client", caplog):
    caplog.set_level(logging.DEBUG)
    """Test disconnected client remains disconnected"""
    await has_state(hrv_client, State.OPEN)
    await asyncio.sleep(1)
    await hrv_client.close()
    await asyncio.sleep(5)
    await has_state(hrv_client, None)
