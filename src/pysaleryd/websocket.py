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


class WSClient:
    """Websocket transport, session handling, message generation."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        callback: Callable[[Signal, str | None, State | None], Awaitable[None]],
    ) -> None:
        """Create resources for websocket communication."""
        self.session = session
        self.host = host
        self.port = port
        self.session_handler_callback = callback

        self.loop = asyncio.get_running_loop()
        self._task = None
        self._ws = None
        self._state = self._previous_state = State.NONE

    @property
    def state(self) -> State:
        """State of websocket."""
        return self._state

    def set_state(self, value: State) -> None:
        """Set state of websocket and store previous state."""
        self._previous_state = self._state
        self._state = value

    def state_changed(self) -> None:
        """Signal state change."""
        asyncio.create_task(
            self.session_handler_callback(
                Signal.CONNECTION_STATE, data=None, state=self._state)
        )

    def start(self) -> None:
        """Start websocket and update its state."""
        if self._state == State.RUNNING:
            _LOGGER.warning("Already running")
            return
        self._task = asyncio.create_task(self.running())

    async def running(self) -> None:
        """Start websocket connection and begin listening"""
        url = f"http://{self.host}:{self.port}"

        try:
            _LOGGER.info("Connecting to websocket (%s:%s)", self.host, self.port)
            self._ws = await self.session.ws_connect(url, timeout=10)
            self.set_state(State.RUNNING)
            self.state_changed()
            _LOGGER.info("Connected to websocket (%s:%s)", self.host, self.port)
            # server won't start sending unless data is received
            await self._ws.send_str("#\r")
            await self._ws.receive_str()

            async for msg in self._ws:

                if msg.type == aiohttp.WSMsgType.CLOSED:
                    _LOGGER.warning(
                        "Connection to websocket closed by remote (%s)", self.host)
                    break

                if msg.type == aiohttp.WSMsgType.ERROR:
                    _LOGGER.error("Websocket error (%s)", self.host)
                    break

                if msg.type == aiohttp.WSMsgType.TEXT:
                    _LOGGER.debug("Received: %s", msg.data)
                    asyncio.create_task(
                        self.session_handler_callback(Signal.DATA, data=msg.data)
                    )
                    continue

                if msg.type != aiohttp.WSMsgType.TEXT:
                    _LOGGER.warning("Received unexpected message type: %s", msg.type)
                    continue

        except aiohttp.ClientError:
            if self._state != State.RETRYING:
                _LOGGER.error("Connection failed (%s)", self.host, exc_info=True)
        except asyncio.CancelledError as exc:
            if self._ws and not self._ws.closed:
                await self._ws.close()
            _LOGGER.debug("Disconnected: %s", exc)

        except Exception as err:
            if self._state != State.RETRYING:
                _LOGGER.error("Unexpected error", exc_info=True)

        self.retry()

    def stop(self) -> None:
        """Close websocket connection."""
        _LOGGER.info("Shutting down connection to websocket (%s)", self.host)
        self.set_state(State.STOPPED)
        self.state_changed()
        self._task.cancel("stop")

    def retry(self) -> None:
        """Retry to connect to websocket.

        Do an immediate retry without timer and without signalling state change.
        Signal state change only after first retry fails.
        """
        if self._state == State.STOPPED:
            return

        if self._state == State.RETRYING and self._previous_state == State.RUNNING:
            _LOGGER.info(
                "Reconnecting to websocket (%s) failed, scheduling retry at an interval of %i seconds",
                self.host,
                RETRY_TIMER,
            )
            self.state_changed()

        self.set_state(State.RETRYING)

        if self._previous_state == State.RUNNING:
            _LOGGER.info("Reconnecting to websocket (%s)", self.host)
            self.start()
            return

        self.loop.call_later(RETRY_TIMER, self.start)

    async def send_message(self, message: str):
        """Send message to websocket"""
        try:
            _LOGGER.debug("Sending message %s to websocket", message)
            return await self._ws.send_str(message)
        except Exception as exc:
            raise Exception(
                f"Failed to send message {message} to websocket. State is {self._state}"
            ) from exc
