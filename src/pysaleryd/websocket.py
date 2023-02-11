"""Python library to connect HRV and Home Assistant to work together."""

from asyncio import create_task, get_running_loop
import datetime
import enum
import logging

from typing import Final, Callable, Awaitable

import aiohttp


LOGGER = logging.getLogger(__package__)


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

        self.loop = get_running_loop()
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
        create_task(
            self.session_handler_callback(Signal.CONNECTION_STATE, data=None, state=self._state)
        )

    def start(self) -> None:
        """Start websocket and update its state."""
        create_task(self.running())

    async def running(self) -> None:
        """Start websocket connection."""
        if self._state == State.RUNNING:
            return

        url = f"http://{self.host}:{self.port}"

        try:
            LOGGER.info("Connecting to websocket (%s:%s)", self.host, self.port)
            self._ws = await self.session.ws_connect(url, timeout=10)
            LOGGER.info("Connected to websocket (%s:%s)", self.host, self.port)
            await self._ws.send_str("#\r") # server won't start sending unless data is received
            await self._ws.receive_str()
            self.set_state(State.RUNNING)
            self.state_changed()

            async for msg in self._ws:
                if self._state == State.STOPPED:
                    await self._ws.close()
                    break

                if msg.type == aiohttp.WSMsgType.TEXT:
                    create_task(
                        self.session_handler_callback(Signal.DATA, data=msg.data)
                    )
                    LOGGER.debug("%s Received: %s", datetime.datetime.now(), msg.data)
                    continue

                if msg.type == aiohttp.WSMsgType.CLOSED:
                    LOGGER.warning("Connection closed (%s)", self.host)
                    break

                if msg.type == aiohttp.WSMsgType.ERROR:
                    LOGGER.error("Websocket error (%s)", self.host)
                    break

        except aiohttp.ClientConnectorError:
            if self._state != State.RETRYING:
                LOGGER.error("Websocket is not accessible (%s)", self.host)

        except Exception as err:
            if self._state != State.RETRYING:
                LOGGER.error("Unexpected error (%s) %s", self.host, err)

        if self._state != State.STOPPED:
            self.retry()

    def stop(self) -> None:
        """Close websocket connection."""
        self.set_state(State.STOPPED)
        LOGGER.info("Shutting down connection to websocket (%s)", self.host)

    def retry(self) -> None:
        """Retry to connect to websocket.

        Do an immediate retry without timer and without signalling state change.
        Signal state change only after first retry fails.
        """
        if self._state == State.RETRYING and self._previous_state == State.RUNNING:
            LOGGER.info(
                "Reconnecting to websocket (%s) failed, scheduling retry at an interval of %i seconds",
                self.host,
                RETRY_TIMER,
            )
            self.state_changed()

        self.set_state(State.RETRYING)

        if self._previous_state == State.RUNNING:
            LOGGER.info("Reconnecting to websocket (%s)", self.host)
            self.start()
            return

        self.loop.call_later(RETRY_TIMER, self.start)

    async def send_message(self, message: str):
        """Send message to websocket"""
        try:
            return await self._ws.send_str(message)
        except Exception as exc:
            raise Exception(
                f"Failed to send message {message} to websocket. State is {self._state}"
            ) from exc
