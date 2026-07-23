"""Memory protocol and bounded in-process reference implementation."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Protocol

from .configuration import MemoryConfiguration
from .errors import MemoryLifecycleError
from .lifecycle import MemoryLifecycle
from .query import MemoryQuery, MemoryResult
from .record import MemoryRecord

_DEFAULT_CONFIGURATION = MemoryConfiguration()
_DEFAULT_QUERY = MemoryQuery()


def _utc_now() -> datetime:
    """Return a timezone-aware UTC instant for local TTL evaluation."""
    return datetime.now(timezone.utc)


class Memory(Protocol):
    """Explicit memory contract; implementations never become agent defaults."""

    @property
    def name(self) -> str: ...

    @property
    def lifecycle(self) -> MemoryLifecycle: ...

    def store(self, record: MemoryRecord) -> None: ...
    def get(
        self, key: str, query: MemoryQuery = _DEFAULT_QUERY
    ) -> MemoryRecord | None: ...
    def delete(self, key: str, query: MemoryQuery = _DEFAULT_QUERY) -> bool: ...
    def list(self, query: MemoryQuery = _DEFAULT_QUERY) -> MemoryResult: ...
    def clear(self, query: MemoryQuery = _DEFAULT_QUERY) -> None: ...
    def snapshot(self) -> MemoryResult: ...
    def close(self) -> None: ...


class ReferenceMemory:
    """Thread-safe, bounded, local-only memory for tests and developer examples."""

    def __init__(
        self,
        name: str = "reference-memory",
        configuration: MemoryConfiguration = _DEFAULT_CONFIGURATION,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not name:
            raise ValueError("Reference memory name must not be empty.")
        self._name = name
        self.configuration = configuration
        self._clock = clock or _utc_now
        self._records: OrderedDict[tuple[str, str | None, str], MemoryRecord] = (
            OrderedDict()
        )
        self._lock = RLock()
        self._closed = False

    @property
    def name(self) -> str:
        """Return this explicit local memory name."""
        return self._name

    @property
    def lifecycle(self) -> MemoryLifecycle:
        """Return active until the caller explicitly closes this memory."""
        return MemoryLifecycle.CLOSED if self._closed else MemoryLifecycle.ACTIVE

    def store(self, record: MemoryRecord) -> None:
        """Store a defensive copy, applying local TTL and oldest-entry eviction."""
        self._ensure_active()
        with self._lock:
            self._purge_expired()
            stored = self._with_default_expiry(record)
            address = self._address(stored)
            self._records.pop(address, None)
            self._records[address] = self._copy(stored)
            while len(self._records) > self.configuration.capacity:
                self._records.popitem(last=False)

    put = store

    def get(self, key: str, query: MemoryQuery = _DEFAULT_QUERY) -> MemoryRecord | None:
        """Return one defensive record copy when its exact local address matches."""
        self._ensure_active()
        with self._lock:
            self._purge_expired()
            for address, record in self._records.items():
                if address[2] == key and self._matches(record, query):
                    return self._copy(record)
        return None

    def delete(self, key: str, query: MemoryQuery = _DEFAULT_QUERY) -> bool:
        """Delete the first matching local record and report whether it existed."""
        self._ensure_active()
        with self._lock:
            self._purge_expired()
            for address, record in self._records.items():
                if address[2] == key and self._matches(record, query):
                    del self._records[address]
                    return True
        return False

    def list(self, query: MemoryQuery = _DEFAULT_QUERY) -> MemoryResult:
        """Return insertion-ordered defensive copies matching a local query."""
        self._ensure_active()
        with self._lock:
            self._purge_expired()
            return MemoryResult(
                tuple(
                    self._copy(record)
                    for record in self._records.values()
                    if self._matches(record, query)
                )
            )

    def query(self, query: MemoryQuery = _DEFAULT_QUERY) -> MemoryResult:
        """Alias explicit local querying to ``list`` without semantic search."""
        return self.list(query)

    def clear(self, query: MemoryQuery = _DEFAULT_QUERY) -> None:
        """Clear all or only matching records without background cleanup work."""
        self._ensure_active()
        with self._lock:
            self._purge_expired()
            if query == _DEFAULT_QUERY:
                self._records.clear()
                return
            for address, record in tuple(self._records.items()):
                if self._matches(record, query):
                    del self._records[address]

    def snapshot(self) -> MemoryResult:
        """Return an isolated stable view of non-expired local records."""
        return self.list()

    def close(self) -> None:
        """Close idempotently and release all locally retained records."""
        with self._lock:
            self._records.clear()
            self._closed = True

    def _ensure_active(self) -> None:
        if self._closed:
            raise MemoryLifecycleError("Reference memory is closed.")

    def _purge_expired(self) -> None:
        now = self._clock()
        for address, record in tuple(self._records.items()):
            if record.expires_at is not None and record.expires_at <= now:
                del self._records[address]

    def _with_default_expiry(self, record: MemoryRecord) -> MemoryRecord:
        if (
            record.expires_at is not None
            or self.configuration.default_ttl_seconds is None
        ):
            return record
        return MemoryRecord(
            record.key,
            record.value,
            record.kind,
            record.metadata,
            record.memory_type,
            record.namespace,
            record.session,
            self._clock() + timedelta(seconds=self.configuration.default_ttl_seconds),
        )

    @staticmethod
    def _address(record: MemoryRecord) -> tuple[str, str | None, str]:
        return (
            record.namespace.name,
            record.session.identifier if record.session else None,
            record.key,
        )

    @staticmethod
    def _copy(record: MemoryRecord) -> MemoryRecord:
        return MemoryRecord(
            record.key,
            deepcopy(record.value),
            record.kind,
            deepcopy(dict(record.metadata)),
            record.memory_type,
            record.namespace,
            record.session,
            record.expires_at,
        )

    @staticmethod
    def _matches(record: MemoryRecord, query: MemoryQuery) -> bool:
        return (
            (query.namespace is None or record.namespace == query.namespace)
            and (query.session is None or record.session == query.session)
            and (query.memory_type is None or record.memory_type == query.memory_type)
            and record.key.startswith(query.key_prefix)
        )
