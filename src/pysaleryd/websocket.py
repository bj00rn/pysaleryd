import asyncio
import logging
from typing import Callable

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed

from .const import ConnectionStateEnum

_LOGGER = logging.getLogger(__name__)


class ReconnectingWebsocketClient:
    """Reconnecting websocket client"""

    def __init__(
        self,
        host: str,
        port: int,
        on_message: callable = None,
        on_state_change: callable = None,
        connect_timeout=15,
    ):
        self._host = host
        self._port = port
        self._connect_timeout = connect_timeout
        self._outgoing_queue: asyncio.Queue[str] = asyncio.Queue()
        self._incoming_queue: asyncio.Queue[str] = asyncio.Queue()
        self._on_message = on_message
        self._on_state_change = on_state_change
        self._state = ConnectionStateEnum.NONE
        self._tasks = []

    @property
    def state(self):
        """State of connection"""
        return self._state

    def _set_state(self, new_state):
        self._state = new_state
        if self._on_state_change:
            self._on_state_change(new_state, self._state)  # is this blocking?

    async def _do_on_message(self, callback: Callable | None):
        while True:
            message = await self._incoming_queue.get()
            if callback:
                callback(message)
            self._incoming_queue.task_done()

    def _do_on_state_change(self, callback: Callable | None):
        if callback:
            callback(self.state)

    async def send(self, message: str):
        """Add message to send queue"""
        if not isinstance(message, str):
            raise ValueError(f"Unsupported message type {type(message)}")
        await self._outgoing_queue.put(message)

    async def runner(self):
        """Send and receive messages on websocket"""

        async def consumer(ws: ClientConnection):
            """Enqueue messages received on websocket"""
            try:
                async for message in ws:
                    if isinstance(message, str):
                        _LOGGER.debug("Message received %s", message)
                        await self._incoming_queue.put(message)
            except asyncio.CancelledError:
                _LOGGER.debug("Consumer was cancelled")
                raise

        async def producer(ws: ClientConnection):
            """Send queued messages on websocket"""
            try:
                while True:
                    message = await self._outgoing_queue.get()
                    _LOGGER.debug("Sending message %s", message)
                    await ws.send(message)
                    self._outgoing_queue.task_done()
            except asyncio.CancelledError:
                _LOGGER.debug("Producer cancelled")
                raise

        async def websocket_handler(websocket: ClientConnection):
            """Websocket handler"""
            try:
                tasks: list[asyncio.Task] = []
                tasks.append(asyncio.create_task(consumer(websocket), name="consumer"))
                tasks.append(asyncio.create_task(producer(websocket), name="producer"))
                await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            finally:
                try:
                    for task in tasks:
                        task.cancel()
                except UnboundLocalError:
                    pass

        uri = f"ws://{self._host}:{self._port}"
        while True:
            try:
                _LOGGER.info("Connecting to %s", uri)
                async for websocket in connect(uri, open_timeout=self._connect_timeout):
                    self._set_state(ConnectionStateEnum.RUNNING)
                    try:
                        _LOGGER.info("Connection established to %s", uri)
                        await websocket_handler(
                            websocket
                        )  # this will return if connection is closed OK by remote
                        _LOGGER.warning("Connection to %s was closed, will retry", uri)
                        self._set_state(ConnectionStateEnum.RETRYING)
                    except ConnectionClosed:
                        _LOGGER.warning(
                            "Connection to %s was closed unexpectedly, will retry", uri
                        )
                        # reconnect if connection fails
                        self._set_state(ConnectionStateEnum.RETRYING)
                        continue

            except (OSError, TimeoutError):
                _LOGGER.error("Failed to connect to %s, will retry", uri)
                self._set_state(ConnectionStateEnum.RETRYING)
                continue
            except asyncio.CancelledError:
                _LOGGER.info("Shutting down connection to %s", uri)
                self._set_state(ConnectionStateEnum.STOPPED)
                raise

    def connect(self):
        """Connect to server"""
        if self._state in [ConnectionStateEnum.NONE, ConnectionStateEnum.STOPPED]:
            self._tasks.append(asyncio.create_task(self.runner(), name="runner"))
            self._tasks.append(
                asyncio.create_task(
                    self._do_on_message(self._on_message), name="on_message"
                )
            )

    def close(self):
        """Close connection and clean up"""
        try:
            pass
        finally:
            for task in self._tasks:
                task.cancel()

    async def __aenter__(self):
        """Start socket and wait for connection"""
        self.connect()
        return self

    async def __aexit__(self, *args, **kwargs):
        self.close()
