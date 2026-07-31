"""Local-first, bounded, advisory TKAI V10 Sovereign Decision Mesh."""
# ruff: noqa: E501

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from tkai.v10.contracts import Scope
from tkai.v10.decision_mesh.contracts import (  # noqa: F401
    CriterionType,
    DecisionConfidence,
    DecisionContext,
    DecisionOption,
    DecisionProfile,
    Dependency,
    Evaluation,
    EvaluationCriterion,
    Limitation,
    LimitationType,
    OptionStatus,
    Recommendation,
    RecommendationStatus,
    Reference,
    Risk,
    Tradeoff,
)
from tkai.v10.decision_mesh.registry import DecisionMeshRegistry
from tkai.v10.decision_mesh.security import filter_secrets, validate_decision_metadata
from tkai.v10.decision_mesh.validation import MAX_RESULT_SIZE, validate_record

SUPPORTED_GENERATIONS = ("v6", "v7", "v8", "v9", "v10")
INTEGRATED_MESHES = (
    "sovereign-core",
    "trust-mesh",
    "integrity-mesh",
    "governance-mesh",
    "compatibility-mesh",
    "knowledge-mesh",
    "reasoning-mesh",
)
METRIC_NAMES = tuple(
    """v10_decision_profiles_total v10_decision_contexts_total v10_decision_options_total
v10_decision_criteria_total v10_decision_evaluations_total v10_decision_tradeoffs_total
v10_decision_recommendations_total v10_decision_confidence_total
v10_decision_validation_failures_total v10_decision_health_status""".split()
)


class SovereignDecisionMesh:
    """Stores decision-reference metadata; never decides, approves, plans, or executes."""

    def __init__(self, *, per_registry_limit: int = 1_000) -> None:
        self.registries = DecisionMeshRegistry(per_registry_limit=per_registry_limit)
        self._audit: list[dict[str, object]] = []
        self._validation_failures = 0
        for generation in SUPPORTED_GENERATIONS:
            self.register(
                "compatibility",
                Reference(
                    f"{generation}-decision",
                    "compatibility-mesh",
                    f"{generation}:completed-components",
                    generation,
                ),
            )
        for mesh in INTEGRATED_MESHES:
            if mesh == "compatibility-mesh":
                # The generation references above already establish this integration.
                continue
            self.register(
                mesh.removesuffix("-mesh").replace("-", "_")
                if mesh != "sovereign-core"
                else "dependencies",
                Reference(f"v10-{mesh}", mesh, f"v10:{mesh}"),
            )

    @staticmethod
    def _safe(record: object) -> None:
        for name in ("safe_metadata", "metrics"):
            metadata = getattr(record, name, None)
            if metadata is not None:
                validate_decision_metadata(metadata)
        for item in fields(record) if is_dataclass(record) and not isinstance(record, type) else ():
            normalized = item.name.casefold()
            if any(
                term in normalized
                for term in ("chain_of_thought", "scratchpad", "hidden_prompt", "token_trace")
            ):
                raise ValueError("hidden reasoning fields are forbidden")

    def register(self, registry: str, record: object) -> object:
        try:
            self._safe(record)
            validate_record(record)
            result = self.registries.get(registry).register(record)
        except (TypeError, ValueError):
            self._validation_failures += 1
            raise
        self._audit.append(
            {
                "action": "decision-metadata-registered",
                "subject": registry,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "read_only": True,
                "advisory": True,
            }
        )
        return result

    def discover(
        self, registry: str, *, scope: Scope | None = None, limit: int = 100
    ) -> tuple[object, ...]:
        if limit < 0 or limit > MAX_RESULT_SIZE:
            raise ValueError("result limit must be between 0 and 100")
        return self.registries.get(registry).discover(scope=scope, limit=limit)

    def health(self) -> dict[str, object]:
        return {
            "status": "healthy",
            "liveness": True,
            "readiness": True,
            "mode": "advisory-read-only",
            "diagnostics": self.diagnostics(),
        }

    def metrics(self) -> dict[str, int]:
        mapping = {
            "profiles": "profiles",
            "contexts": "contexts",
            "options": "options",
            "criteria": "criteria",
            "evaluations": "evaluations",
            "tradeoffs": "tradeoffs",
            "recommendations": "recommendations",
            "confidence": "confidence",
        }
        values = {
            f"v10_decision_{metric}_total": len(self.registries.get(registry))
            for metric, registry in mapping.items()
        }
        values["v10_decision_validation_failures_total"] = self._validation_failures
        values["v10_decision_health_status"] = 1
        return values

    def diagnostics(self) -> dict[str, bool]:
        return {
            name: False
            for name in (
                "decision_execution",
                "automatic_approval",
                "automatic_planning",
                "runtime_mutation",
                "configuration_mutation",
                "storage_mutation",
                "deployment_execution",
                "tiktok_actions",
                "browser_actions",
                "external_network_calls",
                "hidden_reasoning_exposure",
            )
        }

    def audit(self) -> tuple[dict[str, object], ...]:
        return tuple(self._audit)

    def overview(self) -> dict[str, object]:
        return {
            "mesh_id": "tkai-v10-sovereign-decision-mesh",
            "version": "10.0.0",
            "generations": SUPPORTED_GENERATIONS,
            "integrations": INTEGRATED_MESHES,
            "advisory": True,
            "read_only": True,
            "deterministic": True,
            "metadata_driven": True,
            "local_first": True,
            "execution": "disabled",
            "automatic_approval": False,
            "automatic_planning": False,
        }

    @staticmethod
    def serialize(value: Any) -> Any:
        if is_dataclass(value) and not isinstance(value, type):
            value = {item.name: getattr(value, item.name) for item in fields(value)}
        if isinstance(value, dict):
            safe = filter_secrets(value)
            assert isinstance(safe, dict)
            return {str(k): SovereignDecisionMesh.serialize(v) for k, v in safe.items()}
        if isinstance(value, (tuple, list, set, frozenset)):
            return [SovereignDecisionMesh.serialize(v) for v in value]
        if isinstance(value, Enum):
            return value.value
        return value


__all__ = tuple(name for name in globals() if not name.startswith("_"))
