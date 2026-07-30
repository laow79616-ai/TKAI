"""Composition root for the advisory V9 Adaptive Reasoning Mesh."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import cast

from tkai.v8.observability import Observability
from tkai.v9.reasoning_mesh.federation import ReadOnlyFederation
from tkai.v9.reasoning_mesh.registry import RegistryCatalog, ScopedRecord
from tkai.v9.reasoning_mesh.security import secure_metadata


def _serialize(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        result = {
            field.name: _serialize(getattr(value, field.name))
            for field in fields(value)
        }
        if value.__class__.__name__ == "Recommendation":
            result.update({"advisory": True, "executable": False})
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


class AdaptiveReasoningMesh:
    ID = "tkai-v9-adaptive-reasoning-mesh"
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
        self.federation = ReadOnlyFederation(maximum_sources=maximum_sources)
        self.observability = Observability()
        self.observability.audit("reasoning.initialized", "system", self.ID)

    def federate(
        self, sources: tuple[object, ...], actor: str = "system"
    ) -> tuple[object, ...]:
        references = self.federation.federate(sources)  # type: ignore[arg-type]
        self.observability.increment("reasoning.sources.federated", len(references))
        self.observability.audit(
            "reasoning.sources.federated",
            actor,
            self.ID,
            {"references": len(references)},
        )
        return references

    def register(self, resource: str, value: object, actor: str = "system") -> object:
        registry = dict(self.registries.named()).get(resource)
        if registry is None:
            raise ValueError(f"unknown reasoning resource: {resource}")
        registered = registry.register(cast(ScopedRecord, value))
        identifier = next(
            (str(getattr(value, name)) for name in vars(value) if name.endswith("_id")),
            resource,
        )
        self.observability.increment(f"reasoning.{resource}.registered")
        self.observability.audit(f"reasoning.{resource}.registered", actor, identifier)
        return registered

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
            "policies": self.policies(),
            "versions": {"framework": self.VERSION, "immutable": True},
            "compatibility": self.compatibility(),
            "history": self.history(limit),
            "analytics": self.analytics(),
            "diagnostics": self.diagnostics(),
            "health": self.health(),
            "metrics": self.metrics(),
            "audit": self.observability.audit_records(),
        }

    def overview(self) -> dict[str, object]:
        return {
            "mesh_id": self.ID,
            "version": self.VERSION,
            "mode": self.MODE,
            "metadata_only": True,
            "advisory": True,
            "reference_only": True,
            "execution": "disabled",
            "runtime_mutation": "disabled",
            "automatic_approval": "disabled",
            "external_ai": "disabled",
            "hidden_reasoning_storage": "prohibited",
            "hidden_reasoning_retrieval": "prohibited",
            "supported_generations": ("v6", "v7", "v8", "v9"),
            "metadata": dict(self.metadata),
        }

    def governance(self) -> dict[str, object]:
        return {
            "integration_references": (
                "v9_adaptive_governance_mesh",
                "v9_adaptive_meta_kernel",
                "v8_hyper_governance_fabric",
                "v7_runtime_governance_framework",
                "v7_security_framework",
                "v6_autonomous_governance_center",
                "v6_risk_control_center",
            ),
            "runtime_execution": False,
            "pause_aware": True,
            "maintenance_aware": True,
            "kill_switch_aware": True,
        }

    def policies(self) -> dict[str, object]:
        return {
            "advisory_only": True,
            "read_only_federation": True,
            "no_runtime_mutation": True,
            "no_tiktok_action": True,
            "no_browser_action": True,
            "no_external_network": True,
            "no_hidden_reasoning": True,
            "bounded_results": 1000,
        }

    def compatibility(self) -> dict[str, object]:
        kinds = (
            "contract",
            "schema",
            "knowledge",
            "evidence",
            "reasoning_metadata",
            "evaluation",
            "confidence",
            "recommendation",
            "dashboard",
            "api",
            "openapi",
        )
        return {
            "generations": ("v6", "v7", "v8", "v9"),
            "kinds": kinds,
            "automatic_migration": False,
        }

    def history(self, limit: int = 100) -> dict[str, object]:
        return {
            "immutable_versions": True,
            "audit_trail": self.observability.audit_records()[-limit:],
        }

    def analytics(self) -> dict[str, object]:
        counts: dict[str, object] = {
            f"{name}_total": len(registry) for name, registry in self.registries.named()
        }
        scores = [item.score for item in self.registries.evaluations.discover()]
        confidences = [
            item.calibrated_confidence for item in self.registries.confidence.discover()
        ]
        counts.update(
            {
                "validated_evidence_total": len(
                    tuple(
                        item
                        for item in self.registries.evidence.discover()
                        if item.validation_status == "validated"
                    )
                ),
                "rejected_evidence_total": len(
                    tuple(
                        item
                        for item in self.registries.evidence.discover()
                        if item.validation_status == "rejected"
                    )
                ),
                "average_reasoning_quality": sum(scores) / len(scores)
                if scores
                else 0.0,
                "average_calibrated_confidence": (
                    sum(confidences) / len(confidences) if confidences else 0.0
                ),
            }
        )
        return counts

    def diagnostics(self) -> tuple[dict[str, object], ...]:
        findings: list[dict[str, object]] = []
        for hypothesis in self.registries.hypotheses.discover():
            if not hypothesis.falsification_criteria:
                findings.append(
                    {
                        "code": "hypothesis-without-falsification-criteria",
                        "severity": "warning",
                        "hypothesis_id": hypothesis.hypothesis_id,
                    }
                )
        return tuple(findings)

    def health(self) -> dict[str, object]:
        components = (
            "registry",
            "federation",
            "context",
            "source",
            "knowledge",
            "evidence",
            "signal",
            "observation",
            "hypothesis",
            "reasoning",
            "evaluation",
            "confidence",
            "compatibility",
            "governance",
        )
        return {
            "status": "healthy",
            "readiness": True,
            "liveness": True,
            "components": {name: "healthy" for name in components},
            "diagnostics": self.diagnostics(),
        }

    def metrics(self) -> dict[str, object]:
        analytics = self.analytics()
        names = {
            "profiles": "profiles_total",
            "contexts": "contexts_total",
            "sources": "sources_total",
            "knowledge": "knowledge_references_total",
            "evidence": "evidence_total",
            "signals": "signals_total",
            "observations": "observations_total",
            "hypotheses": "hypotheses_total",
            "reasoning": "sessions_total",
            "evaluations": "evaluations_total",
            "recommendations": "recommendations_total",
            "reviews": "reviews_total",
        }
        result = {
            f"v9_reasoning_mesh_{metric}": analytics[f"{resource}_total"]
            for resource, metric in names.items()
        }
        result.update(
            {
                "v9_reasoning_mesh_evidence_validated_total": analytics[
                    "validated_evidence_total"
                ],
                "v9_reasoning_mesh_evidence_rejected_total": analytics[
                    "rejected_evidence_total"
                ],
                "v9_reasoning_mesh_validation_failures_total": 0,
                "v9_reasoning_mesh_confidence": analytics[
                    "average_calibrated_confidence"
                ],
                "v9_reasoning_mesh_confidence_calibration": analytics[
                    "average_calibrated_confidence"
                ],
                "v9_reasoning_mesh_quality": analytics["average_reasoning_quality"],
                "v9_reasoning_mesh_analysis_seconds": 0.0,
                "v9_reasoning_mesh_health_status": 1,
            }
        )
        return result

    @staticmethod
    def executes_tiktok_actions() -> bool:
        return False

    @staticmethod
    def mutates_runtime_state() -> bool:
        return False

    @staticmethod
    def approves_execution() -> bool:
        return False


ReasoningMesh = AdaptiveReasoningMesh

__all__ = ("AdaptiveReasoningMesh", "ReasoningMesh")
