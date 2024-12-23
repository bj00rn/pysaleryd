"""Utils"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .const import MessageType, PayloadSeparator

if TYPE_CHECKING:
    from typing import Optional, Union

    from .const import DataKey

_LOGGER: logging.Logger = logging.getLogger(__package__)


class ParseError(BaseException):
    """Parse error. Raised when message parsing fails"""


@dataclass
class OutgoingMessage:
    """Outgoing message to system"""

    key: DataKey
    value: str

    def __str__(self):
        return f"#{self.key}:{self.value}\r"


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
                    key[1::],
                    payload,
                    MessageType.ACK_OK.value
                    if key[0] == PayloadSeparator.ACK_OK
                    else MessageType.ACK_ERROR.value,
                )
            else:
                return (key, payload, MessageType.MESSAGE.value)
        except Exception as exc:
            raise ParseError(f"Failed to parse message {msg}") from exc


class BaseSystemProperty:
    """HRV System property"""


class SystemProperty(BaseSystemProperty):
    """HRV System property with value, min, max"""

    def __init__(
        self,
        key: DataKey,
        value: Optional[int | str] = None,
        min_value: Optional[int | str] = None,
        max_value: Optional[int | str] = None,
        *_args,
    ):
        self.key = key
        self.value = value
        self.min_value = min_value
        self.max_value = max_value

    @classmethod
    def from_str(cls, key: DataKey, raw_value: str):
        """Create instance from from string"""

        def maybe_cast(x: str) -> Union[int, float, str, None]:
            """Cast value if it is numeric"""
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

        return cls(key, *positions)


class ErrorSystemProperty(BaseSystemProperty):
    """HRV System error property"""

    def __init__(self, key: DataKey, value: Optional[list[str]] = None):
        self.key = key
        self.value = value
