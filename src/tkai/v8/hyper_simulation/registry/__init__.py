"""Thread-safe, isolation-aware immutable metadata registries."""

from __future__ import annotations

from collections.abc import Callable
from threading import RLock
from typing import Generic, TypeVar

from tkai.v8.hyper_simulation import contracts
from tkai.v8.hyper_simulation.contracts import SimulationScope

T = TypeVar("T")


class SimulationRegistry(Generic[T]):
    def __init__(self, name: str, identifier: Callable[[T], str]) -> None:
        self.name = name
        self._identifier = identifier
        self._records: dict[tuple[str, str, str, str, str], T] = {}
        self._lock = RLock()

    def register(self, record: T) -> T:
        scope = record.scope  # type: ignore[attr-defined]
        key = (
            scope.tenant,
            scope.workspace,
            scope.namespace,
            scope.profile,
            self._identifier(record),
        )
        with self._lock:
            if key in self._records:
                raise ValueError(f"duplicate {self.name} metadata: {key[-1]}")
            self._records[key] = record
        return record

    def discover(self, scope: SimulationScope | None = None) -> tuple[T, ...]:
        records = tuple(self._records.values())
        if scope is not None:
            records = tuple(
                item
                for item in records
                if item.scope.tenant == scope.tenant  # type: ignore[attr-defined]
                and item.scope.workspace == scope.workspace  # type: ignore[attr-defined]
                and scope.namespace in {"*", item.scope.namespace}  # type: ignore[attr-defined]
                and scope.profile in {"*", item.scope.profile}  # type: ignore[attr-defined]
            )
        return tuple(sorted(records, key=self._identifier))

    def __len__(self) -> int:
        return len(self._records)


def _identifier(field: str) -> Callable[[object], str]:
    return lambda item: str(getattr(item, field))


class SimulationRegistryCatalog:
    dependencies: SimulationRegistry[contracts.DependencyMetadata]
    DEFINITIONS = (
        ("profiles", contracts.SimulationProfile, "profile_id"),
        ("inputs", contracts.InputMetadata, "input_id"),
        ("baselines", contracts.BaselineMetadata, "baseline_id"),
        ("models", contracts.ModelMetadata, "model_id"),
        ("scenarios", contracts.ScenarioMetadata, "scenario_id"),
        ("simulations", contracts.SimulationMetadata, "simulation_id"),
        ("forecasts", contracts.ForecastMetadata, "forecast_id"),
        ("trends", contracts.TrendMetadata, "trend_id"),
        ("capacity", contracts.CapacityForecastMetadata, "capacity_id"),
        ("resources", contracts.ResourceForecastMetadata, "resource_id"),
        ("schedules", contracts.ScheduleForecastMetadata, "schedule_id"),
        ("dependencies", contracts.DependencyMetadata, "dependency_id"),
        ("risks", contracts.RiskForecastMetadata, "risk_id"),
        ("uncertainty", contracts.UncertaintyMetadata, "uncertainty_id"),
        ("confidence", contracts.ConfidenceMetadata, "confidence_id"),
        ("assumptions", contracts.AssumptionMetadata, "assumption_id"),
        ("constraints", contracts.ConstraintMetadata, "constraint_id"),
        ("comparisons", contracts.ComparisonMetadata, "comparison_id"),
        ("evaluations", contracts.EvaluationMetadata, "evaluation_id"),
        ("recommendations", contracts.RecommendationMetadata, "recommendation_id"),
        ("reviews", contracts.ReviewMetadata, "review_id"),
        ("governance", contracts.GovernanceMetadata, "governance_id"),
        ("compatibility", contracts.CompatibilityMetadata, "compatibility_id"),
    )

    def __init__(self) -> None:
        for name, _kind, identifier in self.DEFINITIONS:
            setattr(
                self,
                name,
                SimulationRegistry(name, _identifier(identifier)),
            )


PlanningRegistry = SimulationRegistry
PlanningRegistryCatalog = SimulationRegistryCatalog
