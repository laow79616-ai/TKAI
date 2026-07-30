"""Immutable metadata contracts for the advisory V8 Hyper Planning Fabric."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

_FORBIDDEN = frozenset(
    {
        "execute",
        "execution",
        "runtime_action",
        "runtime_mutation",
        "automatic_approval",
        "tiktok_action",
        "allocate",
        "schedule_execution",
    }
)


def immutable_metadata(
    values: Mapping[str, object] | None = None,
) -> Mapping[str, object]:
    return MappingProxyType(dict(values or {}))


def reject_active_metadata(values: Mapping[str, object]) -> None:
    for key, value in values.items():
        if str(key).lower() in _FORBIDDEN:
            raise ValueError(
                "active execution, allocation, scheduling, and approval are prohibited"
            )
        if isinstance(value, Mapping):
            reject_active_metadata(value)


class PlanningLifecycle(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    EVALUATED = "evaluated"
    REVIEWED = "reviewed"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class ObjectiveKind(str, Enum):
    BUSINESS = "business"
    OPERATIONAL = "operational"
    GROWTH = "growth"
    RISK = "risk"
    RECOVERY = "recovery"
    RESOURCE = "resource"
    SCHEDULING = "scheduling"
    COMPATIBILITY = "compatibility"


class ConstraintKind(str, Enum):
    GOVERNANCE = "governance"
    SECURITY = "security"
    RUNTIME = "runtime"
    RESOURCES = "resources"
    SCHEDULES = "schedules"
    POLICIES = "policies"
    DEPENDENCIES = "dependencies"
    RISK = "risk"
    COMPATIBILITY = "compatibility"


class DependencyKind(str, Enum):
    FRAMEWORK = "framework"
    CAPABILITY = "capability"
    WORKFLOW = "workflow"
    RESOURCE = "resource"
    COMPATIBILITY = "compatibility"


@dataclass(frozen=True)
class PlanningScope:
    tenant: str = "default"
    workspace: str = "default"
    planning_namespace: str = "default"


@dataclass(frozen=True)
class PlanningReference:
    identifier: str
    version: str = ""
    uri: str = ""
    kind: str = "metadata"
    generation: str = ""
    framework: str = ""
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.identifier or any(char.isspace() for char in self.identifier):
            raise ValueError("reference identifier must not be empty or contain spaces")
        if self.generation not in {"", "v6", "v7", "v8"}:
            raise ValueError("reference generation must be V6, V7, or V8")
        reject_active_metadata(self.metadata)
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class PlanningProfile:
    profile_id: str
    version: str
    owner: str
    objective_references: tuple[PlanningReference, ...] = ()
    constraint_references: tuple[PlanningReference, ...] = ()
    scenario_references: tuple[PlanningReference, ...] = ()
    simulation_references: tuple[PlanningReference, ...] = ()
    resource_references: tuple[PlanningReference, ...] = ()
    schedule_references: tuple[PlanningReference, ...] = ()
    governance_references: tuple[PlanningReference, ...] = ()
    compatibility_references: tuple[PlanningReference, ...] = ()
    health: str = "unknown"
    metrics: Mapping[str, object] = field(default_factory=immutable_metadata)
    audit: tuple[Mapping[str, object], ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: PlanningScope = PlanningScope()
    lifecycle: PlanningLifecycle = PlanningLifecycle.DRAFT

    def __post_init__(self) -> None:
        if not self.profile_id or not self.version or not self.owner:
            raise ValueError("profile_id, version, and owner are required")
        reject_active_metadata(self.metadata)
        object.__setattr__(self, "metrics", immutable_metadata(self.metrics))
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))
        object.__setattr__(
            self, "audit", tuple(immutable_metadata(x) for x in self.audit)
        )

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True)
class ObjectiveMetadata:
    objective_id: str
    kind: ObjectiveKind
    summary: str
    success_criteria: tuple[str, ...] = ()
    scope: PlanningScope = PlanningScope()


@dataclass(frozen=True)
class ConstraintMetadata:
    constraint_id: str
    kind: ConstraintKind
    summary: str
    policy_references: tuple[PlanningReference, ...] = ()
    scope: PlanningScope = PlanningScope()


@dataclass(frozen=True)
class PlanMetadata:
    plan_id: str
    summary: str
    simulation_summary: str = ""
    evaluation_summary: str = ""
    dependency_summary: str = ""
    resource_summary: str = ""
    schedule_summary: str = ""
    recommendation_summary: str = ""
    version_history: tuple[Mapping[str, object], ...] = ()
    scope: PlanningScope = PlanningScope()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "version_history",
            tuple(immutable_metadata(x) for x in self.version_history),
        )

    @property
    def executable(self) -> bool:
        return False


@dataclass(frozen=True)
class ScenarioMetadata:
    scenario_id: str
    summary: str
    expected_outcomes: tuple[str, ...] = ()
    risk_summaries: tuple[str, ...] = ()
    constraint_references: tuple[PlanningReference, ...] = ()
    simulation_references: tuple[PlanningReference, ...] = ()
    scope: PlanningScope = PlanningScope()


@dataclass(frozen=True)
class SimulationMetadata:
    simulation_id: str
    summary: str
    deterministic: bool = True
    capacity_estimate: str = ""
    schedule_estimate: str = ""
    dependency_estimate: str = ""
    scope: PlanningScope = PlanningScope()

    @property
    def offline_only(self) -> bool:
        return True


@dataclass(frozen=True)
class DependencyMetadata:
    dependency_id: str
    kind: DependencyKind
    source: PlanningReference
    target: PlanningReference
    summary: str = ""
    scope: PlanningScope = PlanningScope()


@dataclass(frozen=True)
class ResourceMetadata:
    resource_id: str
    summary: str
    capacity: Mapping[str, object] = field(default_factory=immutable_metadata)
    availability: Mapping[str, object] = field(default_factory=immutable_metadata)
    reservation: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: PlanningScope = PlanningScope()

    def __post_init__(self) -> None:
        for name in ("capacity", "availability", "reservation"):
            value = getattr(self, name)
            reject_active_metadata(value)
            object.__setattr__(self, name, immutable_metadata(value))

    @property
    def allocated(self) -> bool:
        return False


@dataclass(frozen=True)
class ScheduleMetadata:
    schedule_id: str
    summary: str
    planning_windows: tuple[str, ...] = ()
    estimated_duration: str = ""
    milestones: tuple[str, ...] = ()
    scope: PlanningScope = PlanningScope()

    @property
    def scheduler_mutated(self) -> bool:
        return False


@dataclass(frozen=True)
class EvaluationMetadata:
    evaluation_id: str
    subject_reference: PlanningReference
    summary: str = ""
    outcome: str = "not-evaluated"
    scope: PlanningScope = PlanningScope()


@dataclass(frozen=True)
class RecommendationMetadata:
    recommendation_id: str
    summary: str
    plan_references: tuple[PlanningReference, ...] = ()
    governance_references: tuple[PlanningReference, ...] = ()
    limitations: tuple[str, ...] = ()
    scope: PlanningScope = PlanningScope()

    @property
    def advisory(self) -> bool:
        return True

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True)
class ReviewMetadata:
    review_id: str
    subject_reference: PlanningReference
    reviewer_references: tuple[PlanningReference, ...] = ()
    findings: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()
    audit: tuple[Mapping[str, object], ...] = ()
    scope: PlanningScope = PlanningScope()


@dataclass(frozen=True)
class ApprovalMetadata:
    approval_id: str
    subject_reference: PlanningReference
    approver_references: tuple[PlanningReference, ...] = ()
    status: str = "not-reviewed"
    audit: tuple[Mapping[str, object], ...] = ()
    scope: PlanningScope = PlanningScope()

    @property
    def authorizes_execution(self) -> bool:
        return False


@dataclass(frozen=True)
class CompatibilityMetadata:
    compatibility_id: str
    source: PlanningReference
    target: PlanningReference
    status: str = "compatible"
    notes: tuple[str, ...] = ()
    scope: PlanningScope = PlanningScope()


Reference = PlanningReference

__all__ = (
    "ApprovalMetadata",
    "CompatibilityMetadata",
    "ConstraintKind",
    "ConstraintMetadata",
    "DependencyKind",
    "DependencyMetadata",
    "EvaluationMetadata",
    "ObjectiveKind",
    "ObjectiveMetadata",
    "PlanMetadata",
    "PlanningLifecycle",
    "PlanningProfile",
    "PlanningReference",
    "PlanningScope",
    "RecommendationMetadata",
    "Reference",
    "ResourceMetadata",
    "ReviewMetadata",
    "ScenarioMetadata",
    "ScheduleMetadata",
    "SimulationMetadata",
    "immutable_metadata",
    "reject_active_metadata",
)
