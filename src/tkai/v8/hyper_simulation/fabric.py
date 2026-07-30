"""Composition root for advisory, offline V8 simulation and forecasting."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass
from enum import Enum

from tkai.v8.hyper_simulation import contracts
from tkai.v8.hyper_simulation.registry import SimulationRegistryCatalog
from tkai.v8.hyper_simulation.security import secure_metadata
from tkai.v8.observability import Observability


def _serialize(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _serialize(getattr(value, item.name)) for item in fields(value)
        }
    if isinstance(value, Mapping):
        return {
            str(key): _serialize(item) for key, item in secure_metadata(value).items()
        }
    if isinstance(value, (tuple, list)):
        return [_serialize(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    return value


def serialize_record(value: object) -> dict[str, object]:
    result = _serialize(value)
    if not isinstance(result, dict):
        raise TypeError("simulation records must serialize to mappings")
    result["advisory"] = True
    result["execution_authorized"] = False
    if isinstance(value, contracts.SimulationMetadata):
        result["offline_only"] = True
    if isinstance(
        value, (contracts.CapacityForecastMetadata, contracts.ResourceForecastMetadata)
    ):
        result["allocated"] = False
    if isinstance(value, contracts.ScheduleForecastMetadata):
        result["scheduler_mutated"] = False
    if isinstance(value, contracts.RecommendationMetadata):
        result["executable"] = False
    if isinstance(value, contracts.AssumptionMetadata):
        result["is_fact"] = False
    return result


class BoundedSourceAdapter:
    """Copies safe metadata from allowlisted local sources; it has no write surface."""

    def __init__(self, source_id: str, *, maximum_records: int = 100) -> None:
        self.source_id = source_id
        self.maximum_records = maximum_records

    def read(
        self, records: Sequence[Mapping[str, object]]
    ) -> tuple[Mapping[str, object], ...]:
        if len(records) > self.maximum_records:
            raise ValueError("bounded source count exceeded")
        return tuple(secure_metadata(item) for item in records)

    @property
    def read_only(self) -> bool:
        return True


class HyperSimulationFabric:
    ID = "tkai-v8-hyper-simulation"
    VERSION = "8.0.0"
    MODE = "advisory-offline-reference-only"
    MAX_TIME_HORIZON = 3660
    MAX_INPUTS = 1000
    MAX_SCENARIOS = 100
    MAX_SIMULATIONS = 100
    MAX_FORECASTS = 100
    MAX_RESULT_SIZE = 1_000_000
    REGISTRY_NAMES = tuple(item[0] for item in SimulationRegistryCatalog.DEFINITIONS)
    SOURCE_ALLOWLIST = (
        "v8-hyper-kernel",
        "v8-hyper-coordination",
        "v8-hyper-intelligence",
        "v8-hyper-governance",
        "v8-hyper-knowledge",
        "v8-hyper-reasoning",
        "v8-hyper-decision",
        "v8-hyper-planning",
        "v7-frameworks",
        "v6-ai-centers",
    )

    def __init__(self, *, metadata: Mapping[str, object] | None = None) -> None:
        self.metadata = secure_metadata(metadata or {})
        self.registries = SimulationRegistryCatalog()
        self.observability = Observability()
        self._sources: dict[str, tuple[Mapping[str, object], ...]] = {}
        self.observability.audit("simulation.initialized", "system", self.ID)

    def source_adapter(
        self, source_id: str, *, maximum_records: int = 100
    ) -> BoundedSourceAdapter:
        if source_id not in self.SOURCE_ALLOWLIST:
            raise PermissionError("source is not allowlisted")
        return BoundedSourceAdapter(source_id, maximum_records=maximum_records)

    def aggregate_metadata(
        self,
        source_id: str,
        records: Sequence[Mapping[str, object]],
        actor: str = "system",
    ) -> tuple[Mapping[str, object], ...]:
        values = self.source_adapter(source_id).read(records)
        self._sources[source_id] = values
        self.observability.increment("simulation.references.aggregated", len(values))
        self.observability.audit(
            "simulation.metadata.aggregated",
            actor,
            source_id,
            {"references": len(values)},
        )
        return values

    def _register(self, name: str, value: object, actor: str) -> object:
        limits = {
            "inputs": self.MAX_INPUTS,
            "scenarios": self.MAX_SCENARIOS,
            "simulations": self.MAX_SIMULATIONS,
            "forecasts": self.MAX_FORECASTS,
        }
        registry = getattr(self.registries, name)
        if name in limits and len(registry) >= limits[name]:
            raise ValueError(f"bounded {name} count exceeded")
        if isinstance(value, contracts.SimulationProfile):
            self.validate_time_horizon(value.time_horizon)
        if isinstance(value, contracts.ForecastMetadata):
            self.validate_time_horizon(value.horizon)
        result = registry.register(value)
        identifier = next(
            str(getattr(value, item.name))
            for item in fields(value)  # type: ignore[arg-type]
            if item.name.endswith("_id")
        )
        self.observability.increment(f"v8_simulation_{name}_total")
        self.observability.audit(f"simulation.{name}.registered", actor, identifier)
        return result

    def __getattr__(self, name: str) -> object:
        if name.startswith("register_"):
            requested = name.removeprefix("register_")
            registry_name = {
                "profile": "profiles",
                "input": "inputs",
                "baseline": "baselines",
                "model": "models",
                "scenario": "scenarios",
                "simulation": "simulations",
                "forecast": "forecasts",
                "trend": "trends",
                "capacity": "capacity",
                "resource": "resources",
                "schedule": "schedules",
                "dependency": "dependencies",
                "risk": "risks",
                "assumption": "assumptions",
                "constraint": "constraints",
                "comparison": "comparisons",
                "evaluation": "evaluations",
                "recommendation": "recommendations",
                "review": "reviews",
            }.get(requested, requested)
            if registry_name in self.REGISTRY_NAMES:
                return lambda value, actor="system": self._register(
                    registry_name, value, actor
                )
        raise AttributeError(name)

    def validate_time_horizon(self, horizon: int) -> None:
        if not 1 <= horizon <= self.MAX_TIME_HORIZON:
            self.observability.increment("v8_simulation_validation_failures_total")
            raise ValueError("bounded time horizon exceeded")

    def deterministic_forecast(
        self, values: Sequence[float], horizon: int
    ) -> tuple[float, ...]:
        self.validate_time_horizon(horizon)
        if not values or len(values) > self.MAX_INPUTS:
            raise ValueError("bounded non-empty input set required")
        delta = (
            0.0 if len(values) == 1 else (values[-1] - values[0]) / (len(values) - 1)
        )
        return tuple(
            round(values[-1] + delta * step, 10) for step in range(1, horizon + 1)
        )

    def dependency_diagnostics(self) -> tuple[dict[str, object], ...]:
        dependencies = self.registries.dependencies.discover()
        nodes = {item.source.identifier for item in dependencies} | {
            item.target.identifier for item in dependencies
        }
        graph: dict[str, set[str]] = {node: set() for node in nodes}
        diagnostics: list[dict[str, object]] = []
        for item in dependencies:
            graph[item.source.identifier].add(item.target.identifier)
            if not item.available:
                diagnostics.append(
                    {
                        "code": "unavailable-capability",
                        "dependency_id": item.dependency_id,
                    }
                )
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visiting:
                diagnostics.append({"code": "circular-dependency", "reference": node})
                return
            if node in visited:
                return
            visiting.add(node)
            for target in graph[node]:
                visit(target)
            visiting.remove(node)
            visited.add(node)

        for node in sorted(nodes):
            visit(node)
        return tuple(diagnostics)

    def diagnostics(self) -> tuple[dict[str, object], ...]:
        return self.dependency_diagnostics()

    def health(self) -> dict[str, object]:
        return {
            "status": "healthy",
            "mode": self.MODE,
            "registry_health": "healthy",
            "source_adapter_health": "healthy",
            "framework_readiness": True,
            "framework_liveness": True,
            "advisory": True,
            "offline": True,
            "execution": "disabled",
            "runtime_mutation": "disabled",
            "scheduler_mutation": "disabled",
            "resource_allocation": "disabled",
            "network_access": "disabled",
            "diagnostics": self.diagnostics(),
        }

    def metrics(self) -> dict[str, object]:
        names = {
            "profiles": "v8_simulation_profiles_total",
            "inputs": "v8_simulation_inputs_total",
            "baselines": "v8_simulation_baselines_total",
            "models": "v8_simulation_models_total",
            "scenarios": "v8_simulation_scenarios_total",
            "simulations": "v8_simulation_runs_total",
            "forecasts": "v8_simulation_forecasts_total",
            "recommendations": "v8_simulation_recommendations_total",
            "reviews": "v8_simulation_reviews_total",
        }
        values: dict[str, object] = {
            metric: len(getattr(self.registries, registry))
            for registry, metric in names.items()
        }
        values.update(
            {
                "v8_simulation_validation_failures_total": 0,
                "v8_simulation_quality": 0.0,
                "v8_forecast_quality": 0.0,
                "v8_forecast_confidence": 0.0,
                "v8_forecast_confidence_calibration": 0.0,
                "v8_forecast_capacity_accuracy": 0.0,
                "v8_forecast_resource_accuracy": 0.0,
                "v8_forecast_schedule_accuracy": 0.0,
                "v8_forecast_risk_calibration": 0.0,
                "v8_forecast_recovery_accuracy": 0.0,
                "v8_simulation_analysis_seconds": 0.0,
                "v8_simulation_health_status": 1,
            }
        )
        return values

    def analytics(self) -> dict[str, object]:
        return {
            **{
                f"{name}_total": len(getattr(self.registries, name))
                for name in self.REGISTRY_NAMES
            },
            "average_simulation_quality": 0.0,
            "average_forecast_quality": 0.0,
            "average_confidence": 0.0,
            "insufficient_evidence_rate": 0.0,
            "assumption_validation_rate": 0.0,
        }

    def snapshot(self) -> dict[str, object]:
        records = {
            name: [
                serialize_record(item)
                for item in getattr(self.registries, name).discover()
            ]
            for name in self.REGISTRY_NAMES
        }
        return {
            "overview": {
                "fabric_id": self.ID,
                "version": self.VERSION,
                "mode": self.MODE,
                "advisory": True,
                "offline": True,
                "execution_authorized": False,
                "supported_generations": ("v6", "v7", "v8"),
                "metadata": self.metadata,
            },
            **records,
            "validation": {
                "valid": not self.diagnostics(),
                "diagnostics": self.diagnostics(),
            },
            "history": (),
            "analytics": self.analytics(),
            "diagnostics": self.diagnostics(),
            "health": self.health(),
            "metrics": self.metrics(),
            "audit": self.observability.audit_records(),
            "lifecycle": [item.value for item in contracts.SimulationLifecycle],
        }

    @staticmethod
    def executes_tiktok_actions() -> bool:
        return False

    @staticmethod
    def mutates_runtime_state() -> bool:
        return False

    @staticmethod
    def schedules_runtime_work() -> bool:
        return False

    @staticmethod
    def allocates_resources() -> bool:
        return False

    @staticmethod
    def authorizes_execution() -> bool:
        return False

    @staticmethod
    def automatically_approves() -> bool:
        return False

    @staticmethod
    def uses_external_models() -> bool:
        return False


SimulationFabric = HyperSimulationFabric
