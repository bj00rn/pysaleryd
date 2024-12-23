"""Reconnecting websocket client"""
import asyncio
import logging
from typing import Coroutine

from websockets.asyncio.client import ClientConnection, connect, process_exception
from websockets.exceptions import ConnectionClosed
from websockets.protocol import State

from .task import TaskList, task_manager

_LOGGER = logging.getLogger(__name__)


class ReconnectingWebsocketClient:
    """Reconnecting websocket client"""

    def __init__(
        self,
        host: str,
        port: int,
        on_message: Coroutine[None, str, None],
        on_state_change: Coroutine[None, State, None] = None,
        on_connect: Coroutine[None, None, None] = None,
        connect_timeout=15,
    ):
        self._host = host
        self._port = port
        self._connect_timeout = connect_timeout
        self._outgoing_queue: asyncio.Queue[str] = asyncio.Queue()
        self._incoming_queue: asyncio.Queue[str] = asyncio.Queue()
        self._on_message = on_message
        self._on_state_change = on_state_change
        self._on_connect = on_connect
        self._tasks = TaskList()
        self._ws = None

    @property
    def state(self):
        """State of connection"""
        if self._ws:
            return self._ws.protocol.state

    async def _do_on_state_change(self):
        if callable(self._on_state_change):
            await self._on_state_change(self.state)

    async def _do_on_message(self, message: str):
        if callable(self._on_message):
            await self._on_message(message)

    async def _do_on_connect(self):
        if callable(self._on_connect):
            await self._on_connect()

    async def _on_message_runner(self):
        while True:
            message = await self._incoming_queue.get()
            await self._do_on_message(message)
            self._incoming_queue.task_done()

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
            with task_manager(cancel_on_exit=True) as tasks:
                try:
                    tasks.append(
                        asyncio.create_task(consumer(websocket), name="consumer")
                    )
                    tasks.append(
                        asyncio.create_task(producer(websocket), name="producer")
                    )
                finally:
                    await tasks.wait(return_when=asyncio.FIRST_COMPLETED)

        uri = f"ws://{self._host}:{self._port}"
        while True:
            try:
                _LOGGER.info("Connecting to %s", uri)
                async for websocket in connect(uri, open_timeout=self._connect_timeout):
                    try:
                        self._ws = websocket
                        _LOGGER.info("Connection established to %s", uri)
                        await self._do_on_connect()
                        await self._do_on_state_change()
                        await websocket_handler(
                            websocket
                        )  # this will return if connection is closed OK by remote
                        _LOGGER.warning(
                            "Connection to %s was closed, will reconnect", uri
                        )
                        await self._do_on_state_change()
                    except Exception as e:  # pylint: disable=W0718
                        try:
                            await self._do_on_state_change()
                            processed_exception = process_exception(e)
                            if not process_exception:
                                # transient error
                                _LOGGER.error(
                                    "Failed to connect to %s, will retry",
                                    uri,
                                    exc_info=1,
                                )
                                continue
                            else:
                                raise processed_exception  # pylint: disable=W0707
                        except ConnectionClosed:
                            _LOGGER.warning(
                                "Connection to %s was closed unexpectedly, will retry",
                                uri,
                            )
                            # reconnect if connection closed
                            continue

            except asyncio.CancelledError:
                _LOGGER.info("Shutting down connection to %s", uri)
                await self._do_on_state_change()
                raise

    def connect(self):
        """Connect to server"""
        if self._ws is None:
            runner_task = asyncio.create_task(self.runner(), name="runner")
            message_runner_task = asyncio.create_task(self._on_message_runner())
            self._tasks.append(runner_task, message_runner_task)

    def close(self):
        """Close connection and perform clean up"""
        self._tasks.cancel()
        self._ws = None

    def __enter__(self):
        """Initiate connection"""
        self.connect()

    def __exit__(self, *args, **kwargs):
        self.close()
