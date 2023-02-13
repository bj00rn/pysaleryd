"""HRV System client"""

import asyncio
import logging
from typing import Callable

from aiohttp import ClientSession

from .websocket import WSClient, Signal, State

_LOGGER: logging.Logger = logging.getLogger(__package__)

class Client:
    """Client to manage communication with HRV"""

    def __init__(self, url: str, port: int, session: ClientSession):
        self._url = url
        self._port = port
        self._session = session
        self._data = {}
        self._handlers = []
        self._socket = WSClient(self._session, self._url, self._port, self._handler)

    async def __aenter__(self):
        """Start socket and wait for connection"""
        await self.connect()
        return self

    async def __aexit__(self, type, value, traceback):
        self._socket.stop()

    async def connect(self):
        """Connect to system and wait for connection"""
        async def check_connection():
            while self._socket.state != State.RUNNING:
                await asyncio.sleep(0.2)

        self._socket.start()
        await asyncio.wait_for(check_connection(), 10)

    def disconnect(self):
        """Disconnect from system"""
        self._socket.stop()

    def add_handler(self, handler: Callable[[str], None]):
        """Add event handler"""
        self._handlers.append(handler)

    async def _handler(self, signal: Signal, data: str, state: State = None):
        """Call handlers if data"""
        if signal == Signal.DATA:
            for handler in self._handlers:
                try:
                    handler(data)
                except Exception as exc:
                    _LOGGER.warn("Failed to call handler", exc_info=True)

            parsed_message = self._parse_message(data)
            if parsed_message:
                (key, value) = parsed_message
                self._data[key] = value

    def _parse_message(self, msg: str):
        """parse socket message"""
        parsed = None

        try:
            if msg[0] == "#":
                if msg[1] == "$":
                    # ack message, strip ack char and treat as state update
                    msg = msg[1::]
                value = msg[1::].split(":")[1].strip()
                if msg[1] != "*":
                    # messages not beginning with * are arrays of integers
                    # [value, min, max] or [value, min, max, time_left]
                    value = [
                        int(v.strip()) if v.strip().isnumeric() else v.strip()
                        for v in value.split("+")
                    ]
                key = msg[1::].split(":")[0]
                parsed = (key, value)
        except Exception:
            _LOGGER.warning("Failed to parse message %s", msg, exc_info=True)
        return parsed

    @property
    def state(self):
        """Get socket state"""
        return self._socket.state

    @property
    def data(self):
        """Get data"""
        return self._data

    async def async_get_data(self):
        """Async get data"""
        return self.data

    async def send_command(self, key, value: str | int):
        """Send command to HRV"""

        async def ack_command():
            """Should probably ack command here, just sleep for now"""
            await asyncio.sleep(2)

        await self._socket.send_message(f"#{key}:{value}\r")
        await asyncio.gather(ack_command())
