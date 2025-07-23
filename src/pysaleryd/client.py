"""HRV System client"""

import asyncio
import logging
from typing import Callable, Coroutine

from websockets.protocol import State

from .const import DataKey, MessageContext
from .data import Message, ParseError, UnsupportedMessageType
from .helpers.error_cache import ErrorCache
from .helpers.websocket import ReconnectingWebsocketClient

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
        self._on_data_handlers: set[
            Callable[[dict[DataKey, str]], None | Coroutine]
        ] = set()
        self._on_state_change_handlers: set[Callable[[State], None | Coroutine]] = set()
        self._connect_timeout = connect_timeout
        self._tasks = [asyncio.create_task(self._do_call_data_handlers())]
        self._websocket = ReconnectingWebsocketClient(
            host=self._ip,
            port=self._port,
            connect_timeout=self._connect_timeout,
            on_message=self._on_message,
            on_connect=self._send_start_message,
            on_state_change=self._on_state_change,
        )

    @property
    def state(self):
        """State of the underlying websocket connection"""
        return self._websocket.state

    @property
    def data(self):
        """Get data from system if connection is alive"""
        if self.state == State.OPEN:
            return self._data

        return dict()

    async def connect(self):
        """Connect to HRV and begin receiving"""
        await self._websocket.connect()

    async def _send_start_message(self) -> None:
        """Send start message to server to begin receiving data"""
        message = Message(DataKey.NONE, "")
        await self._websocket.send(message.encode())

    async def _do_call_data_handlers(self):
        """Call message handlers with data at update_interval"""
        while True:
            await asyncio.sleep(self._update_interval)
            await self._call_data_handlers()

    async def _call_data_handlers(self):
        """Call handlers with data asynchronously"""
        for handler in self._on_data_handlers:
            try:
                if isinstance(result := handler(self.data), Coroutine):
                    await result
            except BaseException:
                _LOGGER.exception("Failed to call handler %s", handler)

    async def _call_state_change_handlers(self, state):
        """Call state change handlers asynchronously"""
        for handler in self._on_state_change_handlers:
            try:
                if isinstance(result := handler(state), Coroutine):
                    await result
            except BaseException:
                _LOGGER.error("Failed to call handler %s", handler)

    def close(self):
        """Disconnect from system"""
        if self._websocket:
            self._websocket.close()
        for task in self._tasks:
            task.cancel()

    async def _on_state_change(self, state):
        await self._call_state_change_handlers(state)

    async def _on_message(self, msg: str) -> None:
        """Update data"""
        try:
            message = Message.decode(msg)
            if error := self._error_cache.handle(message):
                self._data[DataKey.ERROR_MESSAGE] = str(error)
            else:
                self._data[message.key] = message.payload
                if message.message_context == MessageContext.ACK_OK:
                    await self._call_data_handlers()
        except ParseError as e:
            _LOGGER.error(e, exc_info=True)
        except UnsupportedMessageType as e:
            _LOGGER.debug("Unsupported message type: %s", e, exc_info=True)

    def add_state_change_handler(self, handler: Callable[[State], None | Coroutine]):
        """Add state change handler to be called when client state changes

        :param handler: handler to be added
        :type handler: Callable[[str], None | Coroutine]
        """
        self._on_state_change_handlers.add(handler)

    def remove_state_change_handler(self, handler: Callable[[State], None | Coroutine]):
        """Remove state change handler

        :param handler: handler to be removed
        :type handler: Callable[[str], None | Coroutine]
        """
        self._on_state_change_handlers.remove(handler)

    def add_data_handler(
        self, handler: Callable[[dict[DataKey, str]], None | Coroutine]
    ):
        """Add data handler to be called at update interval

        :param handler: handler function. Must be safe to call from event loop
        :type handler: Callable[[dict[DataKey, str]], None | Coroutine]
        """

        self._on_data_handlers.add(handler)

    def remove_data_handler(
        self, handler: Callable[[dict[DataKey, str]], None | Coroutine]
    ):
        """Remove data handler

        :param handler: handler to remove
        :type handler: Callable[[dict[DataKey, str]], None | Coroutine]
        """
        self._on_data_handlers.remove(handler)

    async def send_command(self, key: DataKey, payload: str | int):
        """Send command to HRV unit

        :param key: message type key
        :type key: MessageType
        :param payload: payload
        :type value: str | int
        """
        message = Message(key, str(payload))

        async def ack_command():
            """Should probably ack command here, just sleep for now"""
            await asyncio.sleep(0.5)

        await self._websocket.send(message.encode())
        await asyncio.gather(ack_command())

    async def __aenter__(self, *args, **kwargs):
        await self.connect()
        return self

    async def __aexit__(self, *args, **kwargs):
        self.close()
        return None
