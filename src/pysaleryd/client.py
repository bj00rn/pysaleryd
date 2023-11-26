"""HRV System client"""

import asyncio
import logging
from typing import Callable

import aiohttp

from .utils import ParseError, Parser
from .websocket import Signal, State, WSClient

_LOGGER: logging.Logger = logging.getLogger(__name__)


class ErrorCache:
    """Error cache, caches prevoius data until frame is complete"""

    def __init__(self) -> None:
        self._data = []
        self._next = []
        self._is_collecting = False

    @property
    def data(self):
        """Get error data"""
        return self._data

    def add(self, message):
        """Add data to cache"""
        if self._is_collecting:
            self._next.append(message)

    def end_frame(self):
        """Mark data frame as complete"""
        self._data = self._next
        self._next = []
        self._is_collecting = False

    def begin_frame(self):
        """Begin new frame"""
        self._is_collecting = True


class Client:
    """Client to manage communication with HRV"""

    def __init__(self, url: str, port: int, session: aiohttp.ClientSession):
        self._url = url
        self._port = port
        self._session = session
        self._data = {}
        self._error_cache = ErrorCache()
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

    def call_handlers(self, data):
        """Call handlers with data"""
        for handler in self._handlers:
            try:
                handler(data)
            except Exception:
                _LOGGER.warning("Failed to call handler", exc_info=True)

    async def _handler(self, signal: Signal, data: str, state: State = None):
        """Call handlers if data"""
        if signal == Signal.DATA:
            try:
                (key, value) = self._parser.from_str(data)

                if key in ["*EA", "*EB", "*EZ"]:
                    if key == "*EA":
                        self._error_cache.begin_frame()
                    if key == "*EB":
                        self._error_cache.add(value)
                    if key == "*EZ":
                        self._error_cache.end_frame()
                        self._data["*EB"] = self._error_cache.data
                        self.call_handlers(("*EB", self._error_cache.data))
                else:
                    self._data[key] = value
                    self.call_handlers(data)
            except ParseError:
                pass

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
