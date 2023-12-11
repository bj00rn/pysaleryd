"""Websocket client to listen and send messages to and from HRV system."""
import asyncio
import enum
import logging
from typing import Awaitable, Callable, Final

import aiohttp

_LOGGER = logging.getLogger(__name__)


class Signal(enum.Enum):
    """What is the content of the callback."""

    CONNECTION_STATE = "state"
    DATA = "data"


class State(enum.Enum):
    """State of the connection."""

    NONE = ""
    RETRYING = "retrying"
    RUNNING = "running"
    STOPPED = "stopped"


RETRY_TIMER: Final = 15
RECEIVE_TIMEOUT: Final = 5
TIMEOUT: Final = 5


class WSClient:
    """Websocket Client"""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        callback: Callable[[Signal, str | None, State | None], Awaitable[None]],
    ) -> None:
        """Create websocket

        Args:
            session (aiohttp.ClientSession): client session
            host (str): system host
            port (int): system port
            callback (Callable[[Signal, str  |  None, State  |  None], Awaitable[None]]): callback for state and data events  # noqa:
        """
        self._session = session
        self._host = host
        self._port = port
        self._session_handler_callback = callback

        self._loop = asyncio.get_running_loop()
        self._task = None
        self._ws = None
        self._state = self._previous_state = State.NONE

    @property
    def state(self) -> State:
        """State of websocket."""
        return self._state

    def _set_state(self, value: State) -> None:
        """Set state of websocket."""
        self._state = value

    def _state_changed(self) -> None:
        """Signal state change."""
        asyncio.create_task(
            self._session_handler_callback(
                Signal.CONNECTION_STATE, data=None, state=self._state
            )
        )

    def _retry(self) -> None:
        """Retry websocket connection"""
        if self._state == State.STOPPED:
            return

        if self._state == State.RETRYING:
            _LOGGER.info(
                "Reconnecting to websocket failed (%s:%s) scheduling retry at an interval of %i seconds",  # noqa: E501
                self._host,
                self._port,
                RETRY_TIMER,
            )
            self._state_changed()
            self._loop.call_later(RETRY_TIMER, self.start)
        else:
            self._set_state(State.RETRYING)
            _LOGGER.info(
                "Reconnecting to websocket (%s:%s)",
                self._host,
                self._port,
            )
            self.start()

    async def _running(self) -> None:
        """Start websocket connection task"""

        try:
            url = f"http://{self._host}:{self._port}"

            try:
                _LOGGER.info("Connecting to websocket (%s:%s)", self._host, self._port)
                self._ws = await self._session.ws_connect(
                    url, timeout=TIMEOUT, receive_timeout=RECEIVE_TIMEOUT
                )
                self._set_state(State.RUNNING)
                self._state_changed()
                _LOGGER.info("Connected to websocket (%s:%s)", self._host, self._port)
                # server won't start sending unless data is received
                await self._ws.send_str("#\r")
                await self._ws.receive_str()

                async for msg in self._ws:
                    if msg.type == aiohttp.WSMsgType.CLOSE:
                        _LOGGER.warning(
                            "Connection to websocket closed by remote (%s:%s)",
                            self._host,
                            self._port,
                        )
                        break

                    if msg.type == aiohttp.WSMsgType.ERROR:
                        _LOGGER.warning("Websocket error (%s)", msg)
                        break

                    if msg.type == aiohttp.WSMsgType.TEXT:
                        _LOGGER.debug("Received: %s", msg.data)
                        asyncio.create_task(
                            self._session_handler_callback(
                                Signal.DATA, data=msg.data, state=self._state
                            )
                        )
                        continue

                    if msg.type != aiohttp.WSMsgType.TEXT:
                        _LOGGER.warning(
                            "Received unexpected message type: %s", msg.type
                        )
                        continue

            except (aiohttp.ClientError, aiohttp.ClientOSError):
                _LOGGER.warning(
                    "Connection failed (%s:%s)", self._host, self._port, exc_info=True
                )
            except asyncio.TimeoutError as exc:
                _LOGGER.warning("Read timeout: %s", exc)
            finally:
                if self._ws:
                    await self._ws.close()
                    _LOGGER.info("Disconnected from (%s:%s)", self._host, self._port)

        except asyncio.CancelledError:
            _LOGGER.debug("Runner cancelled")
            raise
        self._retry()

    def start(self) -> None:
        """Start websocket and update its state."""
        if self._state == State.RUNNING:
            _LOGGER.debug("Already running")
            return
        self._task = asyncio.create_task(self._running())

    def stop(self) -> None:
        """Close websocket connection"""
        _LOGGER.info(
            "Shutting down connection to websocket (%s:%s)", self._host, self._port
        )
        self._set_state(State.STOPPED)
        self._state_changed()
        if self._task:
            self._task.cancel()

    async def send_message(self, message: str):
        """Send message to system

        Args:
            message (str): message

        Returns:
            _type_: Coroutine[Any, Any, None]
        """
        try:
            _LOGGER.debug("Sending message %s to websocket", message)
            return await self._ws.send_str(message)
        except Exception:
            _LOGGER.error(
                "Failed to send message %s to websocket. State is %s",
                message,
                self._state,
                exc_info=True,
            )
            raise
