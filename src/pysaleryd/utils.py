 
import logging

_LOGGER: logging.Logger = logging.getLogger(__package__)


class ParseError(BaseException):
    pass

class Parser():
    def to_str(self, key, value):
        return (f"#{key}:{value}\r")

    def from_str(self, msg: str):
        """parse message"""
        try:
            if msg[0] == "#":
                if msg[1] == "$":
                    # ack message, strip ack char and treat as state update
                    msg = msg[1::]
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
                parsed = (key, value)
                return parsed
        except Exception as exc:
            raise ParseError(f"Failed to parse message {msg}") from exc

        raise ParseError("Failed to parse message {msg}")
