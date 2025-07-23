"""Reconnecting websocket client"""

import asyncio
import logging
from typing import Callable, Coroutine

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
        on_message: Callable[[str], Coroutine[None, str, None]],
        on_state_change: Callable[[str], Coroutine[None, State, None]] | None = None,
        on_connect: Callable[[], Coroutine[None, None, None]] | None = None,
        connect_timeout=15,
    ):
        self._host = host
        self._port = port
        self._connect_timeout = connect_timeout
        self._outgoing_queue: asyncio.Queue[str] = asyncio.Queue()
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
        try:
            if callable(self._on_state_change):
                if isinstance(result := self._on_state_change(self.state), Coroutine):
                    await result
        except BaseException:
            _LOGGER.exception("Error calling on_state_change")

    async def _do_on_message(self, message: str):
        try:
            if callable(self._on_message):
                if isinstance(result := self._on_message(message), Coroutine):
                    await result
        except BaseException:
            _LOGGER.exception("Error calling on_message")

    async def _do_on_connect(self):
        try:
            if callable(self._on_connect):
                if isinstance(result := self._on_connect(), Coroutine):
                    await result
        except BaseException:
            _LOGGER.exception("Error calling on_connect")

    async def send(self, message: str) -> None:
        """Add message to send queue"""
        await self._outgoing_queue.put(message)

    async def runner(self):
        """Send and receive messages on websocket"""
        try:
            uri = f"ws://{self._host}:{self._port}"
            _LOGGER.info("Connecting to %s", uri)
            async for websocket in connect(uri, open_timeout=self._connect_timeout):
                try:
                    self._ws = websocket
                    _LOGGER.info("Connection established to %s", uri)
                    await self._do_on_connect()
                    await self._do_on_state_change()
                    async with task_manager(cancel_on_exit=True) as ws_tasks:
                        consumer_task = asyncio.create_task(
                            self._consumer(websocket), name="consumer"
                        )
                        producer_task = asyncio.create_task(
                            self._producer(websocket), name="producer"
                        )
                        ws_tasks.add(consumer_task, producer_task)
                        await ws_tasks.wait(return_when=asyncio.FIRST_COMPLETED)
                except BaseException as e:  # pylint: disable=W0718
                    if isinstance(e, ConnectionClosed):
                        _LOGGER.warning(
                            "Connection to %s closed by remote host: %s, will retry",
                            uri,
                            e.reason,
                        )
                        continue
                    elif process_exception(e) is None:
                        _LOGGER.warning(
                            "Connection to %s failed due to transient error, will retry",  # noqa: E501
                            uri,
                            exc_info=1,
                        )
                        continue
                    else:
                        raise
                finally:
                    await self._do_on_state_change()

        except asyncio.CancelledError:
            _LOGGER.debug("Shutting down connection to %s", uri)
            raise

    async def _consumer(self, ws: ClientConnection):
        """Enqueue messages received on websocket"""
        try:
            async for message in ws:
                if isinstance(message, str):
                    _LOGGER.debug("Message received %s", message)
                    await self._do_on_message(message)
        except asyncio.CancelledError:
            _LOGGER.debug("Consumer was cancelled")
            raise

    async def _producer(self, ws: ClientConnection):
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

    async def connect(self):
        """Connect to server"""
        if not self._tasks:
            runner_task = asyncio.create_task(self.runner(), name="runner")
            self._tasks.add(runner_task)
        else:
            _LOGGER.warning("Already connected to %s:%s", self._host, self._port)

    def close(self):
        """Close connection and perform clean up"""
        self._tasks.cancel()
        self._ws = None

    def __enter__(self):
        self.connect()

    def __exit__(self, *args, **kwargs):
        self.close()
