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
        on_state_change: (
            Callable[[State | None], Coroutine[None, State | None, None]] | None
        ) = None,
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
        self._initial_connect = asyncio.Event()

    @property
    def state(self) -> State | None:
        """State of connection"""
        if self._ws:
            return self._ws.protocol.state
        return None

    async def __do_on_state_change(self) -> None:
        try:
            if callable(self._on_state_change):
                if isinstance(result := self._on_state_change(self.state), Coroutine):
                    await result
        except BaseException:
            _LOGGER.exception("Error calling on_state_change")

    async def __do_on_message(self, message: str) -> None:
        try:
            if callable(self._on_message):
                if isinstance(result := self._on_message(message), Coroutine):
                    await result
        except BaseException:
            _LOGGER.exception("Error calling on_message")

    async def __do_on_connect(self) -> None:
        try:
            if callable(self._on_connect):
                if isinstance(result := self._on_connect(), Coroutine):
                    await result
        except BaseException:
            _LOGGER.exception("Error calling on_connect")

    async def send(self, message: str) -> None:
        """Add message to send queue"""
        await self._outgoing_queue.put(message)

    def __process_websocket_exception(self, e: Exception) -> Exception | None:
        if not self._initial_connect.is_set():
            # Return exception if initial connection fails
            _LOGGER.debug("Initial connection failed: %s", e)
            return e
        else:
            return process_exception(e)

    async def __runner(self):
        """Send and receive messages on websocket"""
        try:
            uri = f"ws://{self._host}:{self._port}"
            _LOGGER.info("Connecting to %s", uri)
            async for websocket in connect(
                uri,
                open_timeout=self._connect_timeout,
                ping_interval=None,
                process_exception=self.__process_websocket_exception,
            ):
                try:
                    self._ws = websocket
                    _LOGGER.info("Connection established to %s", uri)
                    self._initial_connect.set()
                    await self.__do_on_connect()
                    await self.__do_on_state_change()
                    async with task_manager(cancel_on_exit=True) as ws_tasks:
                        pong_task = asyncio.create_task(
                            self.__keepalive(websocket), name="pong"
                        )
                        consumer_task = asyncio.create_task(
                            self.__consumer(websocket), name="consumer"
                        )
                        producer_task = asyncio.create_task(
                            self.__producer(websocket), name="producer"
                        )
                        ws_tasks.add(consumer_task, producer_task, pong_task)
                        await ws_tasks.wait(return_when=asyncio.FIRST_COMPLETED)
                except ConnectionClosed as e:  # pylint: disable=W0718
                    _LOGGER.warning(
                        "Connection to %s closed by remote host: %s, will retry",
                        uri,
                        e.reason,
                    )
                    continue
                except Exception as e:
                    _LOGGER.error("Error occurred in websocket: %s", e)
                    raise
                finally:
                    await self.__do_on_state_change()
        except asyncio.CancelledError:
            _LOGGER.debug("Shutting down connection to %s", uri)
            raise
        except OSError:
            raise

    async def __consumer(self, ws: ClientConnection) -> None:
        """Enqueue messages received on websocket"""
        try:
            async for message in ws:
                if isinstance(message, str):
                    _LOGGER.debug("Message received %s", message)
                    await self.__do_on_message(message)
        except asyncio.CancelledError:
            _LOGGER.debug("Consumer was cancelled")
            raise

    async def __producer(self, ws: ClientConnection) -> None:
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

    async def __keepalive(self, websocket, pong_interval=float(30)) -> None:
        while True:
            await asyncio.sleep(pong_interval)
            try:
                _LOGGER.debug("Sending keepalive PONG")
                await websocket.send("PONG\r")
            except ConnectionClosed:
                _LOGGER.warning("Connection closed during keepalive, stopping")
                raise

    async def connect(self) -> None:
        """Connect to server"""

        async def waiter(did_connect: asyncio.Event):
            async with asyncio.timeout(self._connect_timeout + 1):
                """Wait for connection to be established"""
                while True:
                    if did_connect.is_set():
                        break
                    await asyncio.sleep(1)

        if not self._tasks:
            runner_task = asyncio.create_task(self.__runner(), name="runner")
            self._tasks.add(runner_task)
            await asyncio.create_task(waiter(self._initial_connect), name="waiter")
        else:
            _LOGGER.warning("Already connected to %s:%s", self._host, self._port)

    async def close(self):
        """Close connection and perform clean up"""
        await self._tasks.cancel()
        self._tasks.clear()
        self._ws = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.close()
