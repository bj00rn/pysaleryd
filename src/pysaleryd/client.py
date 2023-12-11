"""HRV System client"""

import asyncio
import logging
from typing import Callable

import aiohttp

from .utils import ErrorCache, ParseError, Parser
from .websocket import Signal, State, WSClient

_LOGGER: logging.Logger = logging.getLogger(__name__)


class Client:
    """Client to manage communication with HRV"""

    def __init__(
        self, url: str, port: int, session: aiohttp.ClientSession, update_interval=30
    ):
        self._update_interval = update_interval
        self._url = url
        self._port = port
        self._session = session
        self._data = {}
        self._error_cache = ErrorCache()
        self._handlers = set()
        self._socket = WSClient(self._session, self._url, self._port, self._handler)
        self._message_handler_task = asyncio.create_task(self._message_handler())
        self._data_handler_task = asyncio.create_task(self._call_handlers_task())
        self._incoming_queue = asyncio.queues.Queue()

    @property
    def state(self):
        """Get internal socket state"""
        return self._socket.state

    @property
    def data(self):
        """Get data from system"""
        return self._data

    async def __aenter__(self):
        """Start socket and wait for connection"""
        await self.connect()
        return self

    async def __aexit__(self, _type, value, traceback):
        self.disconnect()

    async def _call_handlers_task(self):
        """Call handlers with data"""
        while True:
            self._call_handlers()
            await asyncio.sleep(self._update_interval)

    def _call_handlers(self):
        """Call handlers with data"""
        for handler in self._handlers:
            try:
                handler(self._data)
            except Exception:
                _LOGGER.warning("Failed to call handler", exc_info=True)

    async def _handler(
        self, signal: Signal, data: str, state: "State" = None
    ):  # pylint: disable W0613
        if signal == Signal.DATA:
            await self._incoming_queue.put(data)

    async def _message_handler(self):
        while True:
            try:
                msg = await self._incoming_queue.get()
                # update state
                # if ack force push state to handler
                (key, value, is_ack) = Parser.from_str(msg)

                if key in ["*EA", "*EB", "*EZ"]:
                    if key == "*EA":
                        self._error_cache.begin_frame()
                    if key == "*EB":
                        self._error_cache.add(value)
                    if key == "*EZ":
                        self._error_cache.end_frame()
                        self._data["*EB"] = self._error_cache.data
                else:
                    self._data[key] = value
                    if is_ack:
                        self._call_handlers()
            except ParseError:
                pass

    async def connect(self):
        """Connect to system and wait for connection"""

        async def check_connection():
            while self._socket.state != State.RUNNING:
                await asyncio.sleep(0.2)

        self._socket.start()
        await asyncio.gather(check_connection())

    def disconnect(self):
        """Disconnect from system"""
        self._socket.stop()
        self._data_handler_task.cancel()
        self._message_handler_task.cancel()

    def add_handler(self, handler: Callable[[str], None]):
        """Add event handler"""
        self._handlers.add(handler)

    def remove_handler(self, handler: Callable[[str], None]):
        """Remove event handler"""
        self._handlers.remove(handler)

    async def send_command(self, key, value: str | int):
        """Send command to HRV"""
        message = Parser.to_str(key, value)

        async def ack_command():
            """Should probably ack command here, just sleep for now"""
            await asyncio.sleep(2)

        await self._socket.send_message(message)
        await asyncio.gather(ack_command())
