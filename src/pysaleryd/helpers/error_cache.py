from __future__ import annotations

from pysaleryd.data import DataKey, Message


class ErrorCache:
    """Error cache, caches previous data until frame is complete"""

    def __init__(self) -> None:
        self._current: list[str] = []
        self._next: list[str] = []
        self._is_collecting = False

    def handle(self, message: Message) -> list[str] | None:
        """Handle error message, return error messages if frame is completed"""
        if message.key == DataKey.ERROR_FRAME_START:
            self.__begin_frame()
        elif message.key == DataKey.ERROR_MESSAGE:
            self.__add(message.payload)
        elif message.key == DataKey.ERROR_FRAME_END:
            self.__end_frame()
            return self.data
        # Not an error message
        return None

    @property
    def data(self):
        """Return current error messages

        :return: error messages
        :rtype: list[str]
        """
        return self._current

    def __add(self, message: str):
        """Add error message

        :param message: error message
        :type message: str
        """
        if self._is_collecting:
            self._next.append(message)

    def __end_frame(self):
        """Mark data frame as complete"""
        self._current = self._next
        self._next = []
        self._is_collecting = False

    def __begin_frame(self):
        """Begin new frame"""
        self._is_collecting = True
