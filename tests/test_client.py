import aiohttp
import asyncio
import logging
import pytest
import pytest_asyncio

from pysaleryd.client import Client, State

__author__ = "Björn Dalfors"
__copyright__ = "Björn Dalfors"
__license__ = "MIT"


_LOGGER = logging.getLogger(__package__)

@pytest_asyncio.fixture
async def hrv_client():
    async with aiohttp.ClientSession() as session:
        async with Client("192.168.1.151", 3001, session) as client:
            yield client


@pytest.mark.asyncio
async def test_client_connect(hrv_client):
    """client tests"""
    assert hrv_client.state == State.RUNNING

@pytest.mark.asyncio
async def test_handler(hrv_client, mocker):
    """Test handler callback"""
    handler = mocker.Mock()
    def broken_handler(data):
        raise Exception()
    
    hrv_client.add_handler(broken_handler)
    hrv_client.add_handler(handler)
    await asyncio.sleep(3)
    handler.assert_called()

@pytest.mark.asyncio
async def test_get_data(hrv_client, mocker):
    """Test get data"""
    await asyncio.sleep(1)
    assert isinstance(hrv_client.data, dict)

@pytest.mark.asyncio
async def test_reconnect(hrv_client, mocker):
    """Test reconnect"""
    await hrv_client._socket._ws.close()
    await asyncio.sleep(1)
    assert hrv_client.state == State.RUNNING

@pytest.mark.asyncio
async def test_send_command(hrv_client, mocker):
    """Test send command"""
    await hrv_client.send_command("MF", "0")

@pytest.mark.asyncio
async def test_disconnect(hrv_client: Client, mocker):
    """Test send command"""
    await hrv_client.connect()
    hrv_client.disconnect()
    await asyncio.sleep(2)
