"""Scope-aware registries for immutable planning metadata."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from threading import RLock
from typing import Generic, Protocol, TypeVar, cast

from tkai.v9.planning_mesh.contracts import PlanningScope, Scenario


class ScopedRecord(Protocol):
    @property
    def scope(self) -> PlanningScope: ...


T = TypeVar("T", bound=ScopedRecord)


class Registry(Generic[T]):
    def __init__(self, name: str, identifier: Callable[[T], str]) -> None:
        self.name, self._identifier = name, identifier
        self._records: dict[tuple[str, str, str, str], T] = {}
        self._lock = RLock()

    def register(self, record: T) -> T:
        key = (
            record.scope.tenant,
            record.scope.workspace,
            record.scope.planning,
            self._identifier(record),
        )
        with self._lock:
            if key in self._records:
                raise ValueError(f"duplicate {self.name} record: {key[-1]}")
            self._records[key] = record
        return record

    def discover(
        self, scope: PlanningScope | None = None, limit: int = 100
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
                and scope.planning in {"*", item.scope.planning}
            )
        return tuple(sorted(records, key=self._identifier))[:limit]

    def __len__(self) -> int:
        return len(self._records)


class RegistryCatalog:
    scenarios: Registry[Scenario]

    def __init__(self) -> None:
        definitions = {
            "profiles": "profile_id",
            "objectives": "objective_id",
            "constraints": "constraint_id",
            "assumptions": "assumption_id",
            "plans": "summary_id",
            "scenarios": "scenario_id",
            "simulations": "summary_id",
            "dependencies": "dependency_id",
            "resources": "resource_id",
            "schedules": "schedule_id",
            "evaluations": "summary_id",
            "recommendations": "summary_id",
            "compatibility_records": "compatibility_id",
        }
        for name, identifier in definitions.items():

            def identify(item: ScopedRecord, key: str = identifier) -> str:
                return str(getattr(item, key))

            setattr(self, name, Registry(name, identify))

    def named(self) -> tuple[tuple[str, Registry[ScopedRecord]], ...]:
        names = (
            "profiles",
            "objectives",
            "constraints",
            "assumptions",
            "plans",
            "scenarios",
            "simulations",
            "dependencies",
            "resources",
            "schedules",
            "evaluations",
            "recommendations",
            "compatibility_records",
        )
        return tuple(
            (name, cast(Registry[ScopedRecord], getattr(self, name))) for name in names
        )


__all__ = ("Registry", "RegistryCatalog", "ScopedRecord")
