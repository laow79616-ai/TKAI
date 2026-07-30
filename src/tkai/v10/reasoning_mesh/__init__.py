"""Local-first, bounded, advisory TKAI V10 Sovereign Reasoning Mesh."""
# ruff: noqa: E501

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from tkai.v10.contracts import Scope
from tkai.v10.reasoning_mesh.contracts import (  # noqa: F401
    Alternative,
    Assessment,
    Assumption,
    Claim,
    ClaimType,
    CompatibilityReference,
    Confidence,
    ConstraintReference,
    ConstraintType,
    Contradiction,
    ContradictionType,
    EvidenceReference,
    Explanation,
    Inference,
    InferenceType,
    Premise,
    ReasoningContext,
    ReasoningProfile,
    UncertaintyType,
)
from tkai.v10.reasoning_mesh.registry import ReasoningMeshRegistry
from tkai.v10.reasoning_mesh.security import filter_secrets, validate_reasoning_metadata
from tkai.v10.reasoning_mesh.validation import MAX_RESULT_SIZE, validate_record

SUPPORTED_GENERATIONS = ("v6", "v7", "v8", "v9", "v10")
METRIC_NAMES = tuple(
    """v10_reasoning_profiles_total v10_reasoning_contexts_total
v10_reasoning_claims_total v10_reasoning_premises_total v10_reasoning_evidence_references_total
v10_reasoning_inferences_total v10_reasoning_assumptions_total v10_reasoning_constraints_total
v10_reasoning_alternatives_total v10_reasoning_contradictions_total v10_reasoning_assessments_total
v10_reasoning_validation_failures_total v10_reasoning_health_status
v10_reasoning_assessment_seconds v10_reasoning_explanation_seconds""".split()
)


class SovereignReasoningMesh:
    """Stores caller-supplied reasoning references; never reasons or executes."""

    def __init__(self, *, per_registry_limit: int = 1_000) -> None:
        self.registries = ReasoningMeshRegistry(per_registry_limit=per_registry_limit)
        self._audit: list[dict[str, object]] = []
        self._validation_failures = 0
        for generation in SUPPORTED_GENERATIONS:
            self.register(
                "compatibility",
                CompatibilityReference(
                    f"{generation}-reasoning",
                    generation,
                    f"{generation}:completed-components",
                ),
            )

    @staticmethod
    def _safe(record: object) -> None:
        for name in ("safe_metadata", "metrics"):
            metadata = getattr(record, name, None)
            if metadata is not None:
                validate_reasoning_metadata(metadata)
        for item in (
            fields(record)
            if is_dataclass(record) and not isinstance(record, type)
            else ()
        ):
            normalized = item.name.casefold()
            if any(
                term in normalized
                for term in (
                    "chain_of_thought",
                    "scratchpad",
                    "hidden_prompt",
                    "token_trace",
                )
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
                "action": "reasoning-metadata-registered",
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

    def metrics(self) -> dict[str, int | float]:
        mapping = {
            "profiles": "profiles",
            "contexts": "contexts",
            "claims": "claims",
            "premises": "premises",
            "evidence_references": "evidence",
            "inferences": "inferences",
            "assumptions": "assumptions",
            "constraints": "constraints",
            "alternatives": "alternatives",
            "contradictions": "contradictions",
            "assessments": "assessments",
        }
        values: dict[str, int | float] = {
            f"v10_reasoning_{metric}_total": len(self.registries.get(registry))
            for metric, registry in mapping.items()
        }
        values.update(
            {
                "v10_reasoning_validation_failures_total": self._validation_failures,
                "v10_reasoning_health_status": 1,
                "v10_reasoning_assessment_seconds": 0.0,
                "v10_reasoning_explanation_seconds": 0.0,
            }
        )
        return values

    def diagnostics(self) -> dict[str, bool]:
        return {
            name: False
            for name in (
                "external_network_calls",
                "filesystem_scanning",
                "automatic_ingestion",
                "automatic_decision",
                "automatic_planning",
                "automatic_approval",
                "policy_execution",
                "runtime_mutation",
                "configuration_apply",
                "schema_mutation",
                "storage_mutation",
                "service_control",
                "deployment_execution",
                "tiktok_actions",
                "browser_actions",
                "hidden_chain_of_thought_storage",
                "private_scratchpad_storage",
                "hidden_prompt_exposure",
                "arbitrary_inference_execution",
            )
        }

    def audit(self) -> tuple[dict[str, object], ...]:
        return tuple(self._audit)

    def overview(self) -> dict[str, object]:
        return {
            "mesh_id": "tkai-v10-sovereign-reasoning-mesh",
            "version": "10.0.0",
            "generations": SUPPORTED_GENERATIONS,
            "advisory": True,
            "read_only": True,
            "deterministic": True,
            "metadata_driven": True,
            "local_first": True,
            "execution": "disabled",
            "automatic_selection": False,
        }

    @staticmethod
    def serialize(value: Any) -> Any:
        if is_dataclass(value) and not isinstance(value, type):
            value = {item.name: getattr(value, item.name) for item in fields(value)}
        if isinstance(value, dict):
            safe = filter_secrets(value)
            assert isinstance(safe, dict)
            return {
                str(k): SovereignReasoningMesh.serialize(v) for k, v in safe.items()
            }
        if isinstance(value, (tuple, list, set, frozenset)):
            return [SovereignReasoningMesh.serialize(v) for v in value]
        if isinstance(value, Enum):
            return value.value
        return value


__all__ = tuple(name for name in globals() if not name.startswith("_"))
