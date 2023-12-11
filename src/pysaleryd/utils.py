"""Utils"""
import logging

_LOGGER: logging.Logger = logging.getLogger(__package__)


class ParseError(BaseException):
    """Parse error. Raised when message parsing fails"""


class Parser:
    """Message parser. Parse HRV system messages"""

    @staticmethod
    def to_str(key, value):
        """Parse message to string

        Args:
            key (_type_): message key
            value (_type_): message value

        Returns:
            _type_: _description_
        """
        return f"#{key}:{value}\r"

    @staticmethod
    def from_str(msg: str):
        """Parse message string

        Args:
            msg (str): raw message

        Raises:
            ParseError: if parsing fails

        Returns:
            (key, value): parsed message key and value
        """
        is_ack_message = False
        try:
            if msg[0] == "#":
                if msg[1] == "$":
                    # ack message, strip ack char and treat as state update
                    msg = msg[1::]
                    is_ack_message = True
                value = msg[1::].split(":")[1].strip()
                value = int(value) if value.isnumeric() else value

                if msg[1] != "*":
                    # messages not beginning with * are arrays of integers
                    # [value, min, max] or [value, min, max, time_left]
                    value = [
                        v if isinstance(v, int) else int(v.strip())
                        for v in value.split("+")
                    ]
                key = msg[1::].split(":")[0]
                parsed = (key, value, is_ack_message)
                return parsed
        except Exception as exc:
            raise ParseError(f"Failed to parse message {msg}") from exc

        raise ParseError("Failed to parse message {msg}")


class ErrorCache:
    """Error cache, caches previous data until frame is complete"""

    def __init__(self) -> None:
        self._data = []
        self._next = []
        self._is_collecting = False

    @property
    def data(self):
        """Get error data"""
        return self._data

    def add(self, message):
        """Add data to cache"""
        if self._is_collecting:
            self._next.append(message)

    def end_frame(self):
        """Mark data frame as complete"""
        self._data = self._next
        self._next = []
        self._is_collecting = False

    def begin_frame(self):
        """Begin new frame"""
        self._is_collecting = True
