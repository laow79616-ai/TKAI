"""Isolation-aware registries for immutable planning metadata."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from threading import RLock
from typing import Any, Generic, TypeVar

from tkai.v8.hyper_planning import contracts
from tkai.v8.hyper_planning.contracts import PlanningScope

RecordT = TypeVar("RecordT")


class PlanningRegistry(Generic[RecordT]):
    def __init__(self, name: str, identifier: Callable[[RecordT], str]) -> None:
        self.name = name
        self._identifier = identifier
        self._records: dict[tuple[str, str, str, str], RecordT] = {}
        self._lock = RLock()

    def register(self, record: RecordT) -> RecordT:
        scope = record.scope  # type: ignore[attr-defined]
        key = (
            scope.tenant,
            scope.workspace,
            scope.planning_namespace,
            self._identifier(record),
        )
        with self._lock:
            if key in self._records:
                raise ValueError(f"duplicate {self.name} metadata: {key[-1]}")
            self._records[key] = record
        return record

    def discover(self, scope: PlanningScope | None = None) -> tuple[RecordT, ...]:
        records: Iterable[RecordT] = self._records.values()
        if scope is not None:
            records = (
                item
                for item in records
                if item.scope.tenant == scope.tenant  # type: ignore[attr-defined]
                and item.scope.workspace == scope.workspace  # type: ignore[attr-defined]
                and scope.planning_namespace in {"*", item.scope.planning_namespace}  # type: ignore[attr-defined]
            )
        return tuple(sorted(records, key=self._identifier))

    def __len__(self) -> int:
        return len(self._records)


def _identifier(field: str) -> Callable[[Any], str]:
    return lambda item: str(getattr(item, field))


class PlanningRegistryCatalog:
    constraints: PlanningRegistry[contracts.ConstraintMetadata]
    scenarios: PlanningRegistry[contracts.ScenarioMetadata]

    def __init__(self) -> None:
        definitions = (
            ("profiles", contracts.PlanningProfile, "profile_id"),
            ("objectives", contracts.ObjectiveMetadata, "objective_id"),
            ("constraints", contracts.ConstraintMetadata, "constraint_id"),
            ("plans", contracts.PlanMetadata, "plan_id"),
            ("scenarios", contracts.ScenarioMetadata, "scenario_id"),
            ("simulations", contracts.SimulationMetadata, "simulation_id"),
            ("dependencies", contracts.DependencyMetadata, "dependency_id"),
            ("resources", contracts.ResourceMetadata, "resource_id"),
            ("schedules", contracts.ScheduleMetadata, "schedule_id"),
            ("evaluations", contracts.EvaluationMetadata, "evaluation_id"),
            ("recommendations", contracts.RecommendationMetadata, "recommendation_id"),
            ("reviews", contracts.ReviewMetadata, "review_id"),
            ("approvals", contracts.ApprovalMetadata, "approval_id"),
            ("compatibility", contracts.CompatibilityMetadata, "compatibility_id"),
        )
        for name, _record_type, identifier in definitions:
            setattr(self, name, PlanningRegistry(name, _identifier(identifier)))


__all__ = ("PlanningRegistry", "PlanningRegistryCatalog")
