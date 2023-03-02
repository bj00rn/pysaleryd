"""HRV System client"""

import asyncio
import logging
from typing import Callable
import aiohttp

from .websocket import WSClient, Signal, State
from .utils import ParseError, Parser

_LOGGER: logging.Logger = logging.getLogger(__name__)

class Client:
    """Client to manage communication with HRV"""

    def __init__(self, url: str, port: int, session: aiohttp.ClientSession):
        self._url = url
        self._port = port
        self._session = session
        self._data = {}
        self._handlers = []
        self._socket = WSClient(self._session, self._url, self._port, self._handler)
        self._parser = Parser()

    async def __aenter__(self):
        """Start socket and wait for connection"""
        await self.connect()
        return self

    async def __aexit__(self, type, value, traceback):
        self.disconnect()

    async def connect(self):
        """Connect to system and wait for connection"""
        async def check_connection():
            while self._socket.state != State.RUNNING:
                await asyncio.sleep(0.2)
        try:
            self._socket.start()
            await asyncio.wait_for(check_connection(), 10)
        except Exception as e:
            self.disconnect()
            raise e

    def disconnect(self):
        """Disconnect from system"""
        self._socket.stop()

    def add_handler(self, handler: Callable[[str], None]):
        """Add event handler"""
        self._handlers.append(handler)

    async def _handler(self, signal: Signal, data: str, state: State = None):
        """Call handlers if data"""
        if signal == Signal.DATA:
            try:
                (key, value) = self._parser.from_str(data)
                self._data[key] = value
            except ParseError:
                pass

            for handler in self._handlers:
                try:
                    handler(data)
                except Exception as exc:
                    _LOGGER.warning("Failed to call handler", exc_info=True)

    @property
    def state(self):
        """Get socket internal socket state"""
        return self._socket.state

    @property
    def data(self):
        """Get data from system"""
        return self._data

    async def send_command(self, key, value: str | int):
        """Send command to HRV"""
        message = self._parser.to_str(key, value)
        async def ack_command():
            """Should probably ack command here, just sleep for now"""
            await asyncio.sleep(2)

        await self._socket.send_message(message)
        await asyncio.gather(ack_command())
