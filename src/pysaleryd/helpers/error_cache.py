from __future__ import annotations


class ErrorCache:
    """Error cache, caches previous data until frame is complete"""

    def __init__(self) -> None:
        self._current: list[str] = []
        self._next: list[str] = []
        self._is_collecting = False

    @property
    def data(self):
        """Return current error messages

        :return: error messages
        :rtype: list[str]
        """
        return self._current

    def add(self, message: str):
        """Add error message

        :param message: error message
        :type message: str
        """
        if self._is_collecting:
            self._next.append(message)

    def end_frame(self):
        """Mark data frame as complete"""
        self._current = self._next
        self._next = []
        self._is_collecting = False

    def begin_frame(self):
        """Begin new frame"""
        self._is_collecting = True
