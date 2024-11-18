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
