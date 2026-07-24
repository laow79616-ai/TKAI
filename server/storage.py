"""Storage abstraction protocols and an offline caller-owned reference store."""

from __future__ import annotations

from collections.abc import Iterable
from threading import RLock
from typing import Protocol, TypeVar

T = TypeVar("T")


class ServerStorage(Protocol[T]):
    def get(self, identifier: str) -> T: ...

    def list(self) -> tuple[T, ...]: ...

    def put(self, identifier: str, item: T) -> T: ...

    def remove(self, identifier: str) -> T: ...


RegistryStorage = ServerStorage[object]
PublisherStorage = ServerStorage[object]
PackageStorage = ServerStorage[object]
VersionStorage = ServerStorage[object]
SearchIndexStorage = ServerStorage[object]


class ReferenceStorage:
    """Thread-safe local storage with explicit keys and no persistence."""

    def __init__(self, values: Iterable[tuple[str, object]] = ()) -> None:
        self._lock = RLock()
        self._values = dict(values)

    def get(self, identifier: str) -> object:
        with self._lock:
            return self._values[identifier]

    def list(self) -> tuple[object, ...]:
        with self._lock:
            return tuple(self._values[key] for key in sorted(self._values))

    def put(self, identifier: str, item: object) -> object:
        with self._lock:
            if identifier in self._values:
                raise ValueError(f"Duplicate reference storage key: {identifier}.")
            self._values[identifier] = item
            return item

    def remove(self, identifier: str) -> object:
        with self._lock:
            return self._values.pop(identifier)
