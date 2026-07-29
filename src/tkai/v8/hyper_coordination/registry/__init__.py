"""Thread-safe, scope-isolated coordination metadata registries."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from threading import RLock
from typing import Generic, TypeVar

from tkai.v8.hyper_coordination.contracts import (
    CoordinationProfile,
    CoordinationScope,
    FrameworkDescriptor,
)

RecordT = TypeVar("RecordT")


class CoordinationRegistryError(RuntimeError):
    """Registry contract violation."""


class CoordinationRegistry(Generic[RecordT]):
    """Store immutable metadata records without runtime adapters."""

    def __init__(
        self,
        name: str,
        identifier: Callable[[RecordT], str],
        scope: Callable[[RecordT], CoordinationScope],
    ) -> None:
        self.name = name
        self._identifier = identifier
        self._scope = scope
        self._records: dict[tuple[str, str, str, str], RecordT] = {}
        self._lock = RLock()

    def register(self, record: RecordT) -> RecordT:
        record_scope = self._scope(record)
        key = (
            record_scope.tenant,
            record_scope.workspace,
            record_scope.framework,
            self._identifier(record),
        )
        with self._lock:
            if key in self._records:
                raise CoordinationRegistryError(
                    f"duplicate {self.name} record: {key[-1]}"
                )
            self._records[key] = record
        return record

    def discover(
        self, scope: CoordinationScope | None = None
    ) -> tuple[RecordT, ...]:
        records: Iterable[RecordT] = self._records.values()
        if scope is not None:
            records = (
                record
                for record in records
                if self._scope(record).tenant == scope.tenant
                and self._scope(record).workspace == scope.workspace
                and scope.framework in {"*", self._scope(record).framework}
            )
        return tuple(sorted(records, key=self._identifier))

    def __len__(self) -> int:
        return len(self._records)


class CoordinationRegistryCatalog:
    """Profiles and framework references owned by the coordination layer."""

    def __init__(self) -> None:
        self.profiles: CoordinationRegistry[CoordinationProfile] = CoordinationRegistry(
            "profiles", lambda item: item.profile_id, lambda item: item.scope
        )
        self.frameworks: CoordinationRegistry[FrameworkDescriptor] = (
            CoordinationRegistry(
            "frameworks", lambda item: item.identifier, lambda item: item.scope
            )
        )


ProfileRegistry = CoordinationRegistry[CoordinationProfile]
FrameworkRegistry = CoordinationRegistry[FrameworkDescriptor]

__all__ = (
    "CoordinationRegistry",
    "CoordinationRegistryCatalog",
    "CoordinationRegistryError",
    "FrameworkRegistry",
    "ProfileRegistry",
)
