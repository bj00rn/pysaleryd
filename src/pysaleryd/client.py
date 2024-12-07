"""HRV System client"""

import asyncio
import logging
from typing import Callable

from .const import DataKey, MessageType
from .data import IncomingMessage, OutgoingMessage, ParseError
from .helpers.error_cache import ErrorCache
from .helpers.websocket import ConnectionState, ReconnectingWebsocketClient

_LOGGER: logging.Logger = logging.getLogger(__name__)


class Client:
    """Client to manage communication with HRV"""

    def __init__(
        self, ip: str, port: int = 3001, update_interval=30, connect_timeout=15
    ):
        """Initiate client

        :param ip: ip address of the unit
        :type ip: str
        :param port: port
        :type port: int
        :param update_interval: update interval for calling handler, defaults to 30
        :type update_interval: int, optional
        :param connect_timeout: timeout when establishing connection, defaults to 15
        :type connect_timeout: int, optional
        """
        self._update_interval = update_interval
        self._ip = ip
        self._port = port
        self._data: dict[DataKey, str] = {}
        self._error_cache = ErrorCache()
        self._on_message_handlers: set[Callable[[dict[DataKey, str]]]] = set()
        self._connect_timeout = connect_timeout
        self._state = ConnectionState.NONE
        self._tasks = [asyncio.create_task(self._do_call_message_handlers())]
        self._websocket: ReconnectingWebsocketClient = None

    @property
    def state(self):
        """State of the underlying websocket connection"""
        return self._websocket.state

    @property
    def data(self):
        """Get data from system"""
        return self._data

    def connect(self):
        """Connect to HRV and begin receiving"""

        async def send_start_message():
            # server won't begin sending until message is received
            await self._websocket.send("#:\r")

        self._websocket = ReconnectingWebsocketClient(
            host=self._ip,
            port=self._port,
            connect_timeout=self._connect_timeout,
            on_message=self._on_message,
            on_connect=send_start_message,
        )
        self._websocket.connect()

    async def _do_call_message_handlers(self):
        """Call message handlers with data at update_interval"""
        while True:
            await asyncio.sleep(self._update_interval)
            self._call_message_handlers()

    def _call_message_handlers(self):
        """Call handlers with data"""
        for handler in self._on_message_handlers:
            try:
                handler(self._data)
            except Exception:
                _LOGGER.error("Failed to call handler", exc_info=1)

    def close(self):
        """Disconnect from system"""
        try:
            pass
        finally:
            if self._websocket:
                self._websocket.close()
            for task in self._tasks:
                task.cancel()

    async def _on_message(self, msg: str):
        """Update data"""
        try:
            (key, value, message_type) = IncomingMessage.from_str(msg)

            if key in [
                DataKey.ERROR_FRAME_START,
                DataKey.ERROR_MESSAGE,
                DataKey.ERROR_FRAME_END,
            ]:
                if key == DataKey.ERROR_FRAME_START:
                    self._error_cache.begin_frame()
                if key == DataKey.ERROR_MESSAGE:
                    self._error_cache.add(value)
                if key == DataKey.ERROR_FRAME_END:
                    self._error_cache.end_frame()
                    self._data[DataKey.ERROR_MESSAGE.value] = self._error_cache.data
            else:
                self._data[key] = value
                if message_type == MessageType.ACK_OK:
                    self._call_message_handlers()
        except ParseError as e:
            _LOGGER.warning(e, exc_info=1)

    def add_message_handler(self, handler: Callable[[str], None]):
        """Add message handler

        Message handler will be called at update interval

        :param handler: handler function. Must be safe to call from event loop
        :type handler: Callable[[str], None]
        """
        self._on_message_handlers.add(handler)

    def remove_message_handler(self, handler: Callable[[str], None]):
        """Remove message handler

        :param handler: handler to remove
        :type handler: Callable[[str], None]
        """
        self._on_message_handlers.remove(handler)

    async def send_command(self, key: MessageType, payload: str | int):
        """Send command to HRV unit

        :param key: message type key
        :type key: MessageType
        :param payload: payload
        :type value: str | int
        """
        message = OutgoingMessage(key, payload)

        async def ack_command():
            """Should probably ack command here, just sleep for now"""
            await asyncio.sleep(0.5)

        await self._websocket.send(str(message))
        await asyncio.gather(ack_command())

    def __enter__(self, *args, **kwargs):
        self.connect()
        return self

    def __exit__(self, *args, **kwargs):
        self.close()
