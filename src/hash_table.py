"""A string-keyed hash table using separate chaining."""

import math


class _Node:
    def __init__(self, key: str, value: object, next_node: "_Node | None" = None):
        self.key = key
        self.value = value
        self.next = next_node


class HashTable:
    """Store key/value pairs in a resizable array of linked lists."""

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
        self._buckets: list[_Node | None] = [None] * self._capacity

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
        node = self._buckets[index]
        while node is not None:
            if node.key == key:
                return False
            node = node.next

        self._buckets[index] = _Node(key, value, self._buckets[index])
        self._size += 1
        if self._size / self._capacity > self._max_load_factor:
            self._resize()
        return True

    def get(self, key: str) -> object | None:
        """Return the value for key, or None when key is absent."""
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        node = self._buckets[self._bucket_index(key)]
        while node is not None:
            if node.key == key:
                return node.value
            node = node.next
        return None

    def _iter_items(self):
        for head in self._buckets:
            node = head
            while node is not None:
                yield node.key, node.value
                node = node.next

    def _resize(self) -> None:
        self._capacity *= 2
        buckets: list[_Node | None] = [None] * self._capacity
        for head in self._buckets:
            node = head
            while node is not None:
                next_node = node.next
                index = self._bucket_index(node.key)
                node.next = buckets[index]
                buckets[index] = node
                node = next_node
        self._buckets = buckets
