"""Utils"""

from __future__ import annotations

import logging

from .const import DataKey, MessageContext, MessageSeparator

_LOGGER: logging.Logger = logging.getLogger(__package__)


class ParseError(BaseException):
    """Parse error. Raised when message parsing fails"""


class UnsupportedMessageType(BaseException):
    """Unsupported message type. Raised when message type is not supported"""


class BaseMessage:
    """Base message class"""

    def __init__(
        self,
        key: str | DataKey,
        payload: str,
        message_context: MessageContext = MessageContext.NONE,
    ):
        self.key = DataKey(key)
        self.payload = payload
        self.message_context = message_context


class Message(BaseMessage):
    """Message from HRV system"""

    @classmethod
    def decode(cls, msg: str) -> Message:
        """Decode message from string"""
        try:
            message_context = MessageContext.from_str(msg)
            msg = msg[1::]  # remove first character (message start)

            [key, payload] = [
                v.strip() for v in msg.split(MessageSeparator.PAYLOAD_START, 1)
            ]

            if message_context in [MessageContext.ACK_OK, MessageContext.ACK_ERROR]:
                key = DataKey(key[1::])  # remove first character (ACK type)

            return cls(key, payload, message_context)
        except ValueError as exc:
            raise UnsupportedMessageType() from exc
        except Exception as exc:
            raise ParseError(f"Failed to parse message {msg}") from exc

    def encode(self) -> str:
        """Encode message to string"""
        ps = MessageSeparator
        context = self.message_context._encode()
        return f"{ps.MESSAGE_START}{context}{self.key}{ps.PAYLOAD_START}{self.payload}{ps.MESSAGE_END}"  # noqa: E501


class SystemProperty:
    """HRV System property with value, min, max"""

    def __init__(
        self,
        key: DataKey,
        value: int | str | float | None = None,
        min_value: int | str | float | None = None,
        max_value: int | str | float | None = None,
        extra: int | str | float | None = None,
    ):
        self.key = key
        self.value = value
        self.min_value = min_value
        self.max_value = max_value
        self.extra = extra

    @classmethod
    def from_message(cls, message: Message) -> SystemProperty:
        return cls.from_str(message.key, message.payload)

    @classmethod
    def from_str(cls, key: DataKey, payload: str) -> SystemProperty:
        """Create instance from from string"""

        def maybe_cast(x: str) -> int | float | str | None:
            """Cast value if it is a numeric like string"""
            if x is None:
                return x
            if x.isdigit():
                return int(x)
            if x.replace(".", "", 1).isdigit():
                return float(x)
            return x

        [*positions] = [maybe_cast(v.strip()) for v in payload.split("+")]

        value = positions[0] if len(positions) > 0 else None
        min_value = positions[1] if len(positions) > 1 else None
        max_value = positions[2] if len(positions) > 2 else None
        extra = positions[3] if len(positions) > 3 else None
        return cls(key, value, min_value, max_value, extra)


class ErrorSystemProperty:
    """HRV System error property"""

    def __init__(self, key: DataKey, value: list[str] | None = None):
        self.key = key
        self.value = value
