import asyncio
import aiohttp
import logging
import pytest
import pytest_asyncio

from pysaleryd.client import Client, State

__author__ = "Björn Dalfors"
__copyright__ = "Björn Dalfors"
__license__ = "MIT"

@pytest_asyncio.fixture
async def hrv_client():
    """HRV Client"""
    async with aiohttp.ClientSession() as session:
        async with Client("0.0.0.0", 3001, session) as client:
            yield client

@pytest.mark.asyncio
async def test_client_connect(hrv_client: Client):
    """client tests"""
    assert hrv_client.state == State.RUNNING


@pytest.mark.asyncio
async def test_client_connect_unsresponsive():
    async with aiohttp.ClientSession() as session:  
        client = Client("0.0.0.0", 3002, session)
        try:
            await client.connect()
        except:
            pass

        await asyncio.sleep(10)
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

@pytest.mark.asyncio
async def test_reconnect(hrv_client: Client, mocker):
    """Test reconnect"""
    await hrv_client._socket._ws.close()
    await asyncio.sleep(1)
    assert hrv_client.state == State.RUNNING

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