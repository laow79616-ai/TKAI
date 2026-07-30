"""Bounded, scope-isolated registries for immutable compatibility metadata."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from threading import RLock
from typing import Generic, Protocol, TypeVar, cast

from tkai.v9.compatibility_mesh.contracts import CompatibilityScope


class ScopedRecord(Protocol):
    @property
    def scope(self) -> CompatibilityScope: ...


T = TypeVar("T", bound=ScopedRecord)


class Registry(Generic[T]):
    def __init__(
        self, name: str, identifier: Callable[[T], str], maximum: int = 1000
    ) -> None:
        self.name, self._identifier, self.maximum = name, identifier, maximum
        self._records: dict[tuple[str, str, str, str, str], T] = {}
        self._lock = RLock()

    def register(self, record: T) -> T:
        scope = record.scope
        key = (
            scope.tenant,
            scope.workspace,
            scope.namespace,
            scope.profile,
            self._identifier(record),
        )
        with self._lock:
            if len(self._records) >= self.maximum:
                raise ValueError(f"bounded {self.name} count exceeded")
            if key in self._records:
                raise ValueError(f"duplicate {self.name} record: {key[-1]}")
            self._records[key] = record
        return record

    def discover(
        self, scope: CompatibilityScope | None = None, limit: int = 100
    ) -> tuple[T, ...]:
        if not 0 <= limit <= 1000:
            raise ValueError("result limit must be between 0 and 1000")
        records: Iterable[T] = self._records.values()
        if scope:
            records = (
                item
                for item in records
                if item.scope.tenant == scope.tenant
                and item.scope.workspace == scope.workspace
                and item.scope.namespace == scope.namespace
                and scope.profile in {"*", item.scope.profile}
            )
        return tuple(sorted(records, key=self._identifier))[:limit]

    def __len__(self) -> int:
        return len(self._records)


class RegistryCatalog:
    DEFINITIONS = {
        "profiles": "profile_id",
        "components": "record_id",
        "versions": "record_id",
        "capabilities": "record_id",
        "configurations": "record_id",
        "schemas": "record_id",
        "storage": "record_id",
        "plugins": "record_id",
        "deployments": "record_id",
        "migrations": "record_id",
        "upgrades": "record_id",
        "rollback": "record_id",
        "assessments": "assessment_id",
        "matrices": "matrix_id",
        "recommendations": "recommendation_id",
        "reviews": "review_id",
        "approvals": "approval_id",
        "governance_records": "record_id",
        "compatibility_records": "record_id",
    }

    def __init__(self, maximum_records: int = 1000) -> None:
        for name, identifier in self.DEFINITIONS.items():

            def identify(item: ScopedRecord, key: str = identifier) -> str:
                return str(getattr(item, key))

            setattr(self, name, Registry(name, identify, maximum_records))

    def __getattr__(self, name: str) -> Registry[ScopedRecord]:
        if name not in self.DEFINITIONS:
            raise AttributeError(name)
        return cast(Registry[ScopedRecord], self.__dict__[name])

    def named(self) -> tuple[tuple[str, Registry[ScopedRecord]], ...]:
        return tuple(
            (name, cast(Registry[ScopedRecord], getattr(self, name)))
            for name in self.DEFINITIONS
        )


__all__ = ("Registry", "RegistryCatalog", "ScopedRecord")
