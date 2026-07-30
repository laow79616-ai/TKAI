"""Composition root for the advisory V8 Hyper Autonomous Planning Fabric."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum

from tkai.v8.hyper_planning import contracts
from tkai.v8.hyper_planning.registry import PlanningRegistryCatalog
from tkai.v8.hyper_planning.security import secure_metadata
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
    serialized = _serialize(value)
    if not isinstance(serialized, dict):
        raise TypeError("planning records must serialize to mappings")
    if isinstance(
        value,
        (
            contracts.PlanningProfile,
            contracts.PlanMetadata,
            contracts.RecommendationMetadata,
        ),
    ):
        serialized["execution_authorized"] = False
    if isinstance(value, contracts.PlanMetadata):
        serialized["executable"] = False
    if isinstance(value, contracts.RecommendationMetadata):
        serialized["advisory"] = True
    if isinstance(value, contracts.ApprovalMetadata):
        serialized["authorizes_execution"] = False
    if isinstance(value, contracts.SimulationMetadata):
        serialized["offline_only"] = True
    if isinstance(value, contracts.ResourceMetadata):
        serialized["allocated"] = False
    if isinstance(value, contracts.ScheduleMetadata):
        serialized["scheduler_mutated"] = False
    return serialized


class HyperPlanningFabric:
    """Metadata-driven, advisory planning spanning V6, V7, and V8."""

    ID = "tkai-v8-hyper-planning"
    VERSION = "8.0.0"
    MODE = "reference-only"
    REGISTRY_NAMES = (
        "profiles",
        "objectives",
        "constraints",
        "plans",
        "scenarios",
        "simulations",
        "dependencies",
        "resources",
        "schedules",
        "evaluations",
        "recommendations",
        "reviews",
        "approvals",
        "compatibility",
    )

    def __init__(self, *, metadata: Mapping[str, object] | None = None) -> None:
        self.metadata = secure_metadata(metadata or {})
        self.registries = PlanningRegistryCatalog()
        self.observability = Observability()
        self._sources: dict[str, tuple[Mapping[str, object], ...]] = {
            "v6_ai_centers": (),
            "v7_frameworks": (),
            "v8_frameworks": (),
        }
        self.observability.audit("planning.initialized", "system", self.ID)

    def aggregate_metadata(
        self,
        *,
        v6_ai_centers: tuple[Mapping[str, object], ...] = (),
        v7_frameworks: tuple[Mapping[str, object], ...] = (),
        v8_frameworks: tuple[Mapping[str, object], ...] = (),
        actor: str = "system",
    ) -> dict[str, tuple[Mapping[str, object], ...]]:
        self._sources = {
            "v6_ai_centers": tuple(secure_metadata(x) for x in v6_ai_centers),
            "v7_frameworks": tuple(secure_metadata(x) for x in v7_frameworks),
            "v8_frameworks": tuple(secure_metadata(x) for x in v8_frameworks),
        }
        count = sum(len(items) for items in self._sources.values())
        self.observability.increment("planning.references.aggregated", count)
        self.observability.audit(
            "planning.metadata.aggregated", actor, self.ID, {"references": count}
        )
        return dict(self._sources)

    def _register(
        self, name: str, value: object, identifier: str, actor: str
    ) -> object:
        result = getattr(self.registries, name).register(value)
        self.observability.increment(f"planning.{name}.registered")
        self.observability.audit(f"planning.{name}.registered", actor, identifier)
        return result

    def __getattr__(self, name: str) -> object:
        if name.startswith("register_"):
            requested = name.removeprefix("register_")
            registry_name = {
                "profile": "profiles",
                "objective": "objectives",
                "constraint": "constraints",
                "plan": "plans",
                "scenario": "scenarios",
                "simulation": "simulations",
                "dependency": "dependencies",
                "resource": "resources",
                "schedule": "schedules",
                "evaluation": "evaluations",
                "recommendation": "recommendations",
                "review": "reviews",
                "approval": "approvals",
                "compatibility": "compatibility",
            }.get(requested, requested)
            if registry_name in self.REGISTRY_NAMES:

                def register(value: object, actor: str = "system") -> object:
                    identifier = next(
                        str(getattr(value, field.name))
                        for field in fields(value)  # type: ignore[arg-type]
                        if field.name.endswith("_id")
                    )
                    return self._register(registry_name, value, identifier, actor)

                return register
        raise AttributeError(name)

    def diagnostics(self) -> tuple[dict[str, object], ...]:
        constraint_ids = {
            item.constraint_id for item in self.registries.constraints.discover()
        }
        return tuple(
            {
                "code": "unresolved-constraint-reference",
                "severity": "info",
                "scenario_id": scenario.scenario_id,
                "reference": reference.identifier,
            }
            for scenario in self.registries.scenarios.discover()
            for reference in scenario.constraint_references
            if reference.identifier not in constraint_ids
        )

    def health(self) -> dict[str, object]:
        return {
            "status": "healthy",
            "mode": self.MODE,
            "advisory": True,
            "execution": "disabled",
            "runtime_mutation": "disabled",
            "runtime_scheduling": "disabled",
            "resource_allocation": "disabled",
            "automatic_approval": "disabled",
            "diagnostics": self.diagnostics(),
        }

    def metrics(self) -> dict[str, object]:
        return {
            **{
                name: len(getattr(self.registries, name))
                for name in self.REGISTRY_NAMES
            },
            "aggregated_references": sum(
                len(items) for items in self._sources.values()
            ),
            "counters": self.observability.metrics(),
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
                "metadata_only": True,
                "advisory": True,
                "execution": "disabled",
                "runtime_mutation": "disabled",
                "runtime_scheduling": "disabled",
                "resource_allocation": "disabled",
                "automatic_approval": "disabled",
                "supported_generations": ("v6", "v7", "v8"),
                "metadata": dict(self.metadata),
            },
            **records,
            "sources": {
                name: [_serialize(x) for x in items]
                for name, items in self._sources.items()
            },
            "health": self.health(),
            "metrics": self.metrics(),
            "diagnostics": self.diagnostics(),
            "logs": self.observability.logs(),
            "traces": [serialize_record(x) for x in self.observability.traces()],
            "audit": self.observability.audit_records(),
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


PlanningFabric = HyperPlanningFabric
__all__ = ("HyperPlanningFabric", "PlanningFabric", "serialize_record")
