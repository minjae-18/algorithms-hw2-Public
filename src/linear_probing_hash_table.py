"""A string-keyed hash table using linear probing."""

import math


class _Entry:
    def __init__(self, key: str, value: object):
        self.key = key
        self.value = value


class LinearProbingHashTable:
    """Store key/value pairs in a resizable, open-addressed array."""

    def __init__(
        self, max_load_factor: float = 0.75, *, initial_capacity: int = 8
    ):
        if isinstance(initial_capacity, bool) or not isinstance(initial_capacity, int):
            raise TypeError("initial_capacity must be a positive integer")
        if initial_capacity <= 0:
            raise ValueError("initial_capacity must be a positive integer")
        if isinstance(max_load_factor, bool) or not isinstance(
            max_load_factor, (int, float)
        ):
            raise TypeError("max_load_factor must be a finite positive number")
        try:
            max_load_factor = float(max_load_factor)
        except OverflowError as error:
            raise ValueError(
                "max_load_factor must be a finite positive number"
            ) from error
        if max_load_factor <= 0 or not math.isfinite(max_load_factor):
            raise ValueError("max_load_factor must be a finite positive number")

        self._capacity = initial_capacity
        self._size = 0
        self._max_load_factor = max_load_factor
        self._slots: list[_Entry | None] = [None] * self._capacity

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def size(self) -> int:
        return self._size

    def _bucket_index(self, key: str) -> int:
        value = 0
        for character in key:
            value = (value * 31 + ord(character)) % self._capacity
        return value

    def insert(self, key: str, value: object) -> bool:
        """Insert a new key, leaving an existing value unchanged."""
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        index = self._bucket_index(key)
        for _ in range(self._capacity):
            entry = self._slots[index]
            if entry is None:
                self._slots[index] = _Entry(key, value)
                self._size += 1
                if self._size / self._capacity > self._max_load_factor:
                    self._resize()
                return True
            if entry.key == key:
                return False
            index = (index + 1) % self._capacity

        self._resize()
        return self.insert(key, value)

    def get(self, key: str) -> object | None:
        """Return the value for key, or None when key is absent."""
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        index = self._bucket_index(key)
        for _ in range(self._capacity):
            entry = self._slots[index]
            if entry is None:
                return None
            if entry.key == key:
                return entry.value
            index = (index + 1) % self._capacity
        return None

    def _iter_items(self):
        for entry in self._slots:
            if entry is not None:
                yield entry.key, entry.value

    def _resize(self) -> None:
        entries = list(self._iter_items())
        self._capacity *= 2
        self._size = 0
        self._slots = [None] * self._capacity
        for key, value in entries:
            self.insert(key, value)
