"""HRV System client"""

import asyncio
import logging
from typing import Callable

from .const import DataKeyEnum, MessageTypeEnum
from .helpers import ErrorCache
from .utils import IncomingMessage, OutgoingMessage, ParseError
from .websocket import ConnectionStateEnum, ReconnectingWebsocketClient

_LOGGER: logging.Logger = logging.getLogger(__name__)


class Client:
    """Client to manage communication with HRV"""

    def __init__(self, host: str, port: int, update_interval=30, connect_timeout=15):
        self._update_interval = update_interval
        self._host = host
        self._port = port
        self._data: dict[DataKeyEnum, str] = {}
        self._error_cache = ErrorCache()
        self._handlers: set[Callable[[dict[DataKeyEnum, str]]]] = set()
        self._connect_timeout = connect_timeout
        self._state = ConnectionStateEnum.NONE
        self._tasks = [asyncio.create_task(self._call_handlers_task())]
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

        async def send_start_message(ws: ReconnectingWebsocketClient):
            await ws.send("#:\r")

        self._websocket = ReconnectingWebsocketClient(
            host=self._host,
            port=self._port,
            connect_timeout=self._connect_timeout,
            on_message=self._incoming_message_handler,
        )
        self._websocket.connect()
        self._tasks.append(asyncio.create_task(send_start_message(self._websocket)))

    async def _call_handlers_task(self):
        """Call handlers with data at update_interval"""
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

    def disconnect(self):
        """Disconnect from system"""
        try:
            pass
        finally:
            if self._websocket:
                self._websocket.close()
            for task in self._tasks:
                task.cancel()

    def _incoming_message_handler(self, msg):
        try:
            # update state
            # if ack force push state to handler
            (key, value, message_type) = IncomingMessage.from_str(msg)

            if key in [
                DataKeyEnum.ERROR_FRAME_START,
                DataKeyEnum.ERROR_MESSAGE,
                DataKeyEnum.ERROR_FRAME_END,
            ]:
                if key == DataKeyEnum.ERROR_FRAME_START:
                    self._error_cache.begin_frame()
                if key == DataKeyEnum.ERROR_MESSAGE:
                    self._error_cache.add(value)
                if key == DataKeyEnum.ERROR_FRAME_END:
                    self._error_cache.end_frame()
                    self._data[DataKeyEnum.ERROR_MESSAGE.value] = self._error_cache.data
            else:
                self._data[key] = value
                if message_type == MessageTypeEnum.ACK_OK:
                    self._call_handlers()
        except ParseError:
            pass

    def add_handler(self, handler: Callable[[str], None]):
        """Add event handler"""
        self._handlers.add(handler)

    def remove_handler(self, handler: Callable[[str], None]):
        """Remove event handler"""
        self._handlers.remove(handler)

    async def send_command(self, key: MessageTypeEnum, value: str | int):
        """Send command to HRV"""
        message = OutgoingMessage(key, value)

        async def ack_command():
            """Should probably ack command here, just sleep for now"""
            await asyncio.sleep(0.5)

        await self._websocket.send(str(message))
        await asyncio.gather(ack_command())

    async def __aenter__(self, *args, **kwargs):
        self.connect()
        return self

    async def __aexit__(self, *args, **kwargs):
        self.disconnect()
