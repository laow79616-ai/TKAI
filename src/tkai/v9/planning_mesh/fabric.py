"""Composition root for the advisory V9 Adaptive Planning Mesh."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import cast

from tkai.v8.observability import Observability
from tkai.v9.planning_mesh.contracts import SummaryRecord
from tkai.v9.planning_mesh.federation import ReadOnlyFederation
from tkai.v9.planning_mesh.registry import RegistryCatalog, ScopedRecord
from tkai.v9.planning_mesh.security import secure_metadata


def _serialize(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        result = {
            field.name: _serialize(getattr(value, field.name))
            for field in fields(value)
        }
        if value.__class__.__name__ in {"Plan", "Recommendation"}:
            result["executable"] = False
        if value.__class__.__name__ == "Recommendation":
            result["advisory"] = True
        if value.__class__.__name__ == "Simulation":
            result["executes_runtime"] = False
        if value.__class__.__name__ == "Resource":
            result["allocated"] = False
        if value.__class__.__name__ == "Schedule":
            result["scheduler_mutated"] = False
        if value.__class__.__name__ == "Profile":
            result["execution_authorized"] = False
        return result
    if isinstance(value, Mapping):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_serialize(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    return value


class AdaptivePlanningMesh:
    ID = "tkai-v9-adaptive-planning-mesh"
    VERSION = "9.0.0"
    MODE = "advisory-read-only"

    def __init__(
        self,
        *,
        metadata: Mapping[str, object] | None = None,
        maximum_sources: int = 128,
    ) -> None:
        self.metadata = secure_metadata(metadata or {})
        self.registries = RegistryCatalog()
        self.federation = ReadOnlyFederation(maximum_sources)
        self.observability = Observability()
        self.observability.audit("planning.initialized", "system", self.ID)

    def federate(
        self, sources: tuple[object, ...], actor: str = "system"
    ) -> tuple[object, ...]:
        references = self.federation.federate(sources)  # type: ignore[arg-type]
        self.observability.increment("planning.sources.federated", len(references))
        self.observability.audit(
            "planning.sources.federated",
            actor,
            self.ID,
            {"references": len(references)},
        )
        return references

    def register(self, resource: str, value: object, actor: str = "system") -> object:
        registry = dict(self.registries.named()).get(resource)
        if registry is None:
            raise ValueError(f"unknown planning resource: {resource}")
        registered = registry.register(cast(ScopedRecord, value))
        identifier = next(
            (str(getattr(value, name)) for name in vars(value) if name.endswith("_id")),
            resource,
        )
        self.observability.increment(f"planning.{resource}.registered")
        self.observability.audit(f"planning.{resource}.registered", actor, identifier)
        return registered

    def overview(self) -> dict[str, object]:
        return {
            "mesh_id": self.ID,
            "version": self.VERSION,
            "mode": self.MODE,
            "metadata_only": True,
            "reference_only": True,
            "advisory": True,
            "execution": "disabled",
            "runtime_mutation": "disabled",
            "resource_allocation": "disabled",
            "scheduler_mutation": "disabled",
            "workflow_triggering": "disabled",
            "tiktok_actions": "disabled",
            "supported_generations": ("v6", "v7", "v8", "v9"),
            "metadata": dict(self.metadata),
        }

    def compatibility(self) -> dict[str, object]:
        return {
            "generations": ("v6", "v7", "v8", "v9"),
            "reference_only": True,
            "automatic_migration": False,
        }

    def governance(self) -> dict[str, object]:
        return {
            "governance_references": (
                "v9_adaptive_governance_mesh",
                "v8_hyper_governance_fabric",
                "v7_runtime_governance_framework",
                "v6_autonomous_governance_center",
            ),
            "rbac_compatible": True,
            "approves_execution": False,
            "runtime_execution": False,
        }

    def analytics(self) -> dict[str, object]:
        return {
            f"{name}_total": len(registry) for name, registry in self.registries.named()
        }

    def diagnostics(self) -> tuple[dict[str, object], ...]:
        return tuple(
            {
                "code": "scenario-limitations-missing",
                "severity": "warning",
                "scenario_id": item.scenario_id,
            }
            for item in self.registries.scenarios.discover()
            if not item.limitations
        )

    def health(self) -> dict[str, object]:
        components = (
            "registry",
            "federation",
            "objectives",
            "constraints",
            "scenarios",
            "simulations",
            "dependencies",
            "resources",
            "schedules",
            "recommendations",
            "compatibility",
            "security",
            "audit",
        )
        return {
            "status": "healthy",
            "readiness": True,
            "liveness": True,
            "components": {name: "healthy" for name in components},
            "diagnostics": self.diagnostics(),
        }

    def metrics(self) -> dict[str, object]:
        metrics: dict[str, object] = {
            f"v9_planning_mesh_{name}_total": len(registry)
            for name, registry in self.registries.named()
        }
        metrics.update(
            {
                "v9_planning_mesh_federated_references_total": len(
                    self.federation.references()
                ),
                "v9_planning_mesh_health_status": 1,
                "v9_planning_mesh_execution_total": 0,
                "v9_planning_mesh_resource_allocations_total": 0,
                "v9_planning_mesh_scheduler_mutations_total": 0,
            }
        )
        return metrics

    def history(self, limit: int = 100) -> dict[str, object]:
        registries = dict(self.registries.named())
        version_references = [
            _serialize(cast(SummaryRecord, item).version_history)
            for name in ("plans", "simulations", "evaluations", "recommendations")
            for item in registries[name].discover(limit=limit)
        ]
        return {
            "immutable": True,
            "version_references": version_references,
            "audit_trail": self.observability.audit_records()[-limit:],
        }

    def snapshot(self, limit: int = 100) -> dict[str, object]:
        records = {
            name: [_serialize(item) for item in registry.discover(limit=limit)]
            for name, registry in self.registries.named()
        }
        records["compatibility"] = records.pop("compatibility_records")
        return {
            "overview": self.overview(),
            **records,
            "federation": [_serialize(item) for item in self.federation.references()],
            "governance": self.governance(),
            "history": self.history(limit),
            "analytics": self.analytics(),
            "diagnostics": self.diagnostics(),
            "health": self.health(),
            "metrics": self.metrics(),
            "audit": self.observability.audit_records(),
        }

    @staticmethod
    def executes_tiktok_actions() -> bool:
        return False

    @staticmethod
    def mutates_runtime_state() -> bool:
        return False

    @staticmethod
    def allocates_resources() -> bool:
        return False

    @staticmethod
    def mutates_scheduler() -> bool:
        return False

    @staticmethod
    def triggers_workflows() -> bool:
        return False

    @staticmethod
    def approves_execution() -> bool:
        return False


PlanningMesh = AdaptivePlanningMesh
__all__ = ("AdaptivePlanningMesh", "PlanningMesh")
