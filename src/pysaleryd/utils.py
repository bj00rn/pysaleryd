"""Utils"""
import logging
from dataclasses import dataclass
from typing import Any

from .const import DataKeyEnum, MessageTypeEnum, PayloadSeparatorEnum

_LOGGER: logging.Logger = logging.getLogger(__package__)


class ParseError(BaseException):
    """Parse error. Raised when message parsing fails"""


@dataclass
class OutgoingMessage:
    """Outgoing message to system"""

    key: DataKeyEnum
    value: str

    def __str__(self):
        return f"#{self.key}:{self.value}\r"


class IncomingMessage:
    """Incoming message from system"""

    @staticmethod
    def from_str(msg: str) -> tuple[DataKeyEnum, str, MessageTypeEnum]:
        """Parse message string

        Args:
            msg (str): raw message

        Raises:
            ParseError: if parsing fails

        Returns:
            (key, value, message_type): parsed message key and value
        """
        if msg[0] != PayloadSeparatorEnum.MESSAGE_START:
            raise ParseError(f"Unsupported payload, {msg}")
        else:
            msg = msg[1::]
        try:
            [key, payload] = [
                v.strip() for v in msg.split(PayloadSeparatorEnum.PAYLOAD_START)
            ]

            if key[0] in [PayloadSeparatorEnum.ACK_ERROR, PayloadSeparatorEnum.ACK_OK]:
                return (
                    key[1::],
                    payload,
                    MessageTypeEnum.ACK_OK.value
                    if key[0] == PayloadSeparatorEnum.ACK_OK
                    else MessageTypeEnum.ACK_ERROR.value,
                )
            else:
                return (key, payload, MessageTypeEnum.MESSAGE.value)
        except Exception as exc:
            raise ParseError(f"Failed to parse message {msg}") from exc


@dataclass
class SystemProperty:
    """HRV system property"""

    key: DataKeyEnum = None
    value: Any = None

    @classmethod
    def from_str(cls, key, raw_value):
        """Create instance from string"""
        return cls(key=key, value=raw_value.strip())


@dataclass
class RangedSystemProperty(SystemProperty):
    """HRV System property with min max"""

    min_value: int = None
    max_value: int = None
    time_left: int = None

    @classmethod
    def from_str(cls, key, raw_value: str):
        """Create instance from from string"""
        [value, min_value, max_value, time_left] = [
            int(v) if v.isnumeric() else int(v.strip()) for v in raw_value.split("+")
        ]
        return cls(
            key=key,
            value=value,
            min_value=min_value,
            max_value=max_value,
            time_left=time_left,
        )


@dataclass
class ErrorSystemProperty(SystemProperty):
    key: DataKeyEnum
    value: list[str]

    @classmethod
    def from_str(cls, key, raw_value):
        raise NotImplementedError()
