"""Typed immutable-record registries."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Generic, TypeVar

from tkai.v8.hyper_recovery import contracts

T = TypeVar("T")


class MetadataRegistry(Generic[T]):
    def __init__(self, identifier: Callable[[T], str]) -> None:
        self._identifier = identifier
        self._records: dict[str, T] = {}

    def register(self, value: T) -> T:
        identifier = self._identifier(value)
        if identifier in self._records:
            raise ValueError(
                f"immutable metadata record already registered: {identifier}"
            )
        self._records[identifier] = value
        return value

    def get(self, identifier: str) -> T:
        return self._records[identifier]

    def discover(self, maximum_results: int = 500) -> tuple[T, ...]:
        if maximum_results < 0 or maximum_results > 500:
            raise ValueError("bounded result size exceeded")
        return tuple(self._records[key] for key in sorted(self._records))[
            :maximum_results
        ]

    def __len__(self) -> int:
        return len(self._records)


class RecoveryRegistryCatalog:
    DEFINITIONS = (
        ("profiles", contracts.RecoveryProfile, "profile_id"),
        ("incidents", contracts.IncidentMetadata, "incident_id"),
        ("failures", contracts.FailureClassification, "failure_id"),
        ("impact", contracts.ImpactAssessment, "impact_id"),
        ("readiness", contracts.ReadinessAssessment, "readiness_id"),
        ("resilience", contracts.ResilienceAssessment, "resilience_id"),
        ("continuity", contracts.ContinuityMetadata, "continuity_id"),
        ("plans", contracts.RecoveryPlan, "recovery_plan_id"),
        ("steps", contracts.RecoveryStep, "step_id"),
        ("rollback", contracts.RollbackPlan, "rollback_plan_id"),
        ("snapshots", contracts.SnapshotMetadata, "snapshot_id"),
        ("checkpoints", contracts.CheckpointMetadata, "checkpoint_id"),
        ("restoration", contracts.AdvisoryArtifact, "artifact_id"),
        ("degraded", contracts.AdvisoryArtifact, "artifact_id"),
        ("dependencies", contracts.AdvisoryArtifact, "artifact_id"),
        ("resources", contracts.AdvisoryArtifact, "artifact_id"),
        ("capacity", contracts.AdvisoryArtifact, "artifact_id"),
        ("validation", contracts.AdvisoryArtifact, "artifact_id"),
        ("evaluations", contracts.Evaluation, "evaluation_id"),
        ("recommendations", contracts.AdvisoryArtifact, "artifact_id"),
        ("reviews", contracts.Review, "review_id"),
        ("approvals", contracts.Approval, "approval_id"),
        ("governance", contracts.AdvisoryArtifact, "artifact_id"),
        ("compatibility", contracts.AdvisoryArtifact, "artifact_id"),
        ("history", contracts.AdvisoryArtifact, "artifact_id"),
        ("health_records", contracts.AdvisoryArtifact, "artifact_id"),
        ("metric_records", contracts.AdvisoryArtifact, "artifact_id"),
    )

    def __init__(self) -> None:
        for name, _record_type, identifier in self.DEFINITIONS:

            def identify(value: Any, key: str = identifier) -> str:
                return str(getattr(value, key))

            setattr(
                self,
                name,
                MetadataRegistry(identify),
            )
