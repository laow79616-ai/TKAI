"""Composition root for the advisory V9 Adaptive Decision Mesh."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import cast

from tkai.v8.observability import Observability
from tkai.v9.decision_mesh.federation import ReadOnlyFederation
from tkai.v9.decision_mesh.registry import RegistryCatalog, ScopedRecord
from tkai.v9.decision_mesh.security import secure_metadata


def _serialize(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        result = {
            field.name: _serialize(getattr(value, field.name))
            for field in fields(value)
        }
        if value.__class__.__name__ == "Decision":
            result["executable"] = False
        if value.__class__.__name__ == "Recommendation":
            result.update({"advisory": True, "executable": False})
        if value.__class__.__name__ == "Approval":
            result["authorizes_execution"] = False
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


class AdaptiveDecisionMesh:
    ID = "tkai-v9-adaptive-decision-mesh"
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
        self.observability.audit("decision.initialized", "system", self.ID)

    def federate(
        self, sources: tuple[object, ...], actor: str = "system"
    ) -> tuple[object, ...]:
        references = self.federation.federate(sources)  # type: ignore[arg-type]
        self.observability.increment("decision.sources.federated", len(references))
        self.observability.audit(
            "decision.sources.federated",
            actor,
            self.ID,
            {"references": len(references)},
        )
        return references

    def register(self, resource: str, value: object, actor: str = "system") -> object:
        registry = dict(self.registries.named()).get(resource)
        if registry is None:
            raise ValueError(f"unknown decision resource: {resource}")
        registered = registry.register(cast(ScopedRecord, value))
        identifier = next(
            (str(getattr(value, name)) for name in vars(value) if name.endswith("_id")),
            resource,
        )
        self.observability.increment(f"decision.{resource}.registered")
        self.observability.audit(f"decision.{resource}.registered", actor, identifier)
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
            "automatic_approval": "disabled",
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
            "approval_authorizes_execution": False,
            "runtime_execution": False,
        }

    def analytics(self) -> dict[str, object]:
        counts: dict[str, object] = {
            f"{name}_total": len(registry) for name, registry in self.registries.named()
        }
        values = [item.value for item in self.registries.confidence.discover()]
        counts["average_confidence"] = sum(values) / len(values) if values else 0.0
        return counts

    def diagnostics(self) -> tuple[dict[str, object], ...]:
        return tuple(
            {
                "code": "confidence-limitations-missing",
                "severity": "warning",
                "confidence_id": item.confidence_id,
            }
            for item in self.registries.confidence.discover()
            if not item.limitations
        )

    def health(self) -> dict[str, object]:
        components = (
            "registry",
            "federation",
            "decisions",
            "alternatives",
            "comparisons",
            "recommendations",
            "confidence",
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
            f"v9_decision_mesh_{name}_total": len(registry)
            for name, registry in self.registries.named()
        }
        metrics.update(
            {
                "v9_decision_mesh_federated_references_total": len(
                    self.federation.references()
                ),
                "v9_decision_mesh_average_confidence": self.analytics()[
                    "average_confidence"
                ],
                "v9_decision_mesh_health_status": 1,
                "v9_decision_mesh_execution_total": 0,
            }
        )
        return metrics

    def history(self, limit: int = 100) -> dict[str, object]:
        return {
            "immutable": True,
            "version_references": [
                _serialize(item.version_history)
                for item in self.registries.decisions.discover(limit=limit)
            ],
            "audit_trail": self.observability.audit_records()[-limit:],
        }

    def snapshot(self, limit: int = 100) -> dict[str, object]:
        records = {
            name: [_serialize(item) for item in registry.discover(limit=limit)]
            for name, registry in self.registries.named()
        }
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
    def approves_execution() -> bool:
        return False


DecisionMesh = AdaptiveDecisionMesh
__all__ = ("AdaptiveDecisionMesh", "DecisionMesh")
