"""Utils"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from .const import DataKey, MessageType, PayloadSeparator

_LOGGER: logging.Logger = logging.getLogger(__package__)


class ParseError(BaseException):
    """Parse error. Raised when message parsing fails"""


@dataclass
class OutgoingMessage:
    """Outgoing message to system"""

    key: DataKey
    value: str | int

    def __str__(self):
        ps = PayloadSeparator
        return f"{ps.MESSAGE_START}{self.key}{ps.PAYLOAD_START}{self.value}{ps.MESSAGE_END}"  # noqa: E501


class IncomingMessage:
    """Incoming message from system"""

    @staticmethod
    def from_str(msg: str) -> tuple[DataKey, str, MessageType]:
        """Parse message string

        Args:
            msg (str): raw message

        Raises:
            ParseError: if parsing fails

        Returns:
            (key, value, message_type): parsed message key and value
        """
        if msg[0] != PayloadSeparator.MESSAGE_START:
            raise ParseError(f"Unsupported payload, {msg}")
        else:
            msg = msg[1::]
        try:
            [key, payload] = [
                v.strip() for v in msg.split(PayloadSeparator.PAYLOAD_START, 1)
            ]

            if key[0] in [PayloadSeparator.ACK_ERROR, PayloadSeparator.ACK_OK]:
                return (
                    DataKey(key[1::]),
                    payload,
                    MessageType.ACK_OK
                    if key[0] == PayloadSeparator.ACK_OK
                    else MessageType.ACK_ERROR,
                )
            else:
                return (DataKey(key), payload, MessageType.MESSAGE)
        except Exception as exc:
            raise ParseError(f"Failed to parse message {msg}") from exc


class BaseSystemProperty:
    """HRV System property"""


class SystemProperty(BaseSystemProperty):
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
    def from_str(cls, key: DataKey, raw_value: str):
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

        [*positions] = (
            [maybe_cast(v.strip()) for v in raw_value.split("+")]
            if raw_value is not None
            else []
        )

        value = positions[0] if len(positions) > 0 else None
        min_value = positions[1] if len(positions) > 1 else None
        max_value = positions[2] if len(positions) > 2 else None
        extra = positions[3] if len(positions) > 3 else None
        return cls(key, value, min_value, max_value, extra)

    def to_str(self) -> str:
        """Convert to string"""
        ps = PayloadSeparator
        if self.min_value is not None and self.max_value is not None:
            return f"{ps.MESSAGE_START}{self.key}+{self.value}+{self.min_value}+{self.max_value}{ps.MESSAGE_END}"  # noqa: E501
        return f"{ps.MESSAGE_START}{self.key}{ps.PAYLOAD_START}{str(self.value)}{ps.MESSAGE_END}"  # noqa: E501


class ErrorSystemProperty(BaseSystemProperty):
    """HRV System error property"""

    def __init__(self, key: DataKey, value: list[str] | None = None):
        self.key = key
        self.value = value
