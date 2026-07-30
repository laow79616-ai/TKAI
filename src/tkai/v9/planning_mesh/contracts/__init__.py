"""Immutable, advisory contracts for the V9 Adaptive Planning Mesh."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

SECRET_KEYS = frozenset(
    {"access_token", "api_key", "authorization", "cookie", "password", "secret"}
)


def safe_metadata(values: Mapping[str, object] | None = None) -> Mapping[str, object]:
    copied = dict(values or {})
    for key, value in copied.items():
        normalized = str(key).lower().replace("-", "_")
        if normalized in SECRET_KEYS or any(part in normalized for part in SECRET_KEYS):
            raise ValueError("secret-bearing metadata is prohibited")
        if isinstance(value, Mapping):
            safe_metadata(value)
    return MappingProxyType(copied)


class PlanningLifecycle(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    UNDER_REVIEW = "under_review"
    REVIEWED = "reviewed"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class PlanningScope:
    tenant: str = "default"
    workspace: str = "default"
    planning: str = "*"


@dataclass(frozen=True)
class Reference:
    identifier: str
    version: str = ""
    kind: str = "metadata"
    generation: str = ""
    framework: str = ""
    metadata: Mapping[str, object] = field(default_factory=safe_metadata)

    def __post_init__(self) -> None:
        if not self.identifier or any(char.isspace() for char in self.identifier):
            raise ValueError("reference identifier must not be empty or contain spaces")
        object.__setattr__(self, "metadata", safe_metadata(self.metadata))


@dataclass(frozen=True)
class Profile:
    profile_id: str
    version: str
    owner: str
    objective_references: tuple[Reference, ...] = ()
    constraint_references: tuple[Reference, ...] = ()
    scenario_references: tuple[Reference, ...] = ()
    simulation_references: tuple[Reference, ...] = ()
    resource_references: tuple[Reference, ...] = ()
    schedule_references: tuple[Reference, ...] = ()
    governance_references: tuple[Reference, ...] = ()
    compatibility_references: tuple[Reference, ...] = ()
    health: str = "unknown"
    metrics: Mapping[str, object] = field(default_factory=safe_metadata)
    audit: tuple[Mapping[str, object], ...] = ()
    metadata: Mapping[str, object] = field(default_factory=safe_metadata)
    scope: PlanningScope = PlanningScope()

    def __post_init__(self) -> None:
        if not all((self.profile_id, self.version, self.owner)):
            raise ValueError("profile_id, version, and owner are required")
        object.__setattr__(self, "metrics", safe_metadata(self.metrics))
        object.__setattr__(self, "metadata", safe_metadata(self.metadata))
        object.__setattr__(self, "audit", tuple(safe_metadata(x) for x in self.audit))

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True)
class SummaryRecord:
    summary_id: str
    summary: str
    references: tuple[Reference, ...] = ()
    limitations: tuple[str, ...] = ()
    version_history: tuple[Reference, ...] = ()
    version: str = "1.0.0"
    scope: PlanningScope = PlanningScope()


@dataclass(frozen=True)
class Objective:
    objective_id: str
    category: str
    summary: str
    references: tuple[Reference, ...] = ()
    scope: PlanningScope = PlanningScope()

    def __post_init__(self) -> None:
        if self.category not in {
            "business",
            "operations",
            "recovery",
            "security",
            "governance",
            "compatibility",
        }:
            raise ValueError("unsupported objective category")


CONSTRAINT_CATEGORIES = frozenset(
    {
        "governance",
        "security",
        "runtime",
        "resources",
        "schedules",
        "dependencies",
        "risk",
        "compatibility",
        "pause",
        "maintenance",
        "kill_switch",
    }
)


@dataclass(frozen=True)
class Constraint:
    constraint_id: str
    category: str
    summary: str
    references: tuple[Reference, ...] = ()
    scope: PlanningScope = PlanningScope()

    def __post_init__(self) -> None:
        if self.category not in CONSTRAINT_CATEGORIES:
            raise ValueError("unsupported constraint category")


@dataclass(frozen=True)
class Assumption:
    assumption_id: str
    summary: str
    evidence_references: tuple[Reference, ...] = ()
    limitations: tuple[str, ...] = ()
    scope: PlanningScope = PlanningScope()


@dataclass(frozen=True)
class Plan(SummaryRecord):
    @property
    def executable(self) -> bool:
        return False


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    summary: str
    expected_outcomes: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    risk_summaries: tuple[str, ...] = ()
    simulation_references: tuple[Reference, ...] = ()
    scope: PlanningScope = PlanningScope()


@dataclass(frozen=True)
class Simulation(SummaryRecord):
    deterministic: bool = True

    @property
    def executes_runtime(self) -> bool:
        return False


@dataclass(frozen=True)
class Dependency:
    dependency_id: str
    category: str
    summary: str
    references: tuple[Reference, ...] = ()
    scope: PlanningScope = PlanningScope()


@dataclass(frozen=True)
class Resource:
    resource_id: str
    summary: str
    capacity_metadata: Mapping[str, object] = field(default_factory=safe_metadata)
    availability_metadata: Mapping[str, object] = field(default_factory=safe_metadata)
    reservation_metadata: Mapping[str, object] = field(default_factory=safe_metadata)
    forecast_references: tuple[Reference, ...] = ()
    scope: PlanningScope = PlanningScope()

    def __post_init__(self) -> None:
        for name in (
            "capacity_metadata",
            "availability_metadata",
            "reservation_metadata",
        ):
            object.__setattr__(self, name, safe_metadata(getattr(self, name)))

    @property
    def allocated(self) -> bool:
        return False


@dataclass(frozen=True)
class Schedule:
    schedule_id: str
    summary: str
    planning_windows: tuple[str, ...] = ()
    estimated_duration: str = ""
    milestones: tuple[str, ...] = ()
    review_windows: tuple[str, ...] = ()
    approval_windows: tuple[str, ...] = ()
    scope: PlanningScope = PlanningScope()

    @property
    def scheduler_mutated(self) -> bool:
        return False


@dataclass(frozen=True)
class Evaluation(SummaryRecord):
    pass


@dataclass(frozen=True)
class Recommendation(SummaryRecord):
    @property
    def advisory(self) -> bool:
        return True

    @property
    def executable(self) -> bool:
        return False


@dataclass(frozen=True)
class Compatibility:
    compatibility_id: str
    generation: str
    subject_reference: Reference
    status: str = "compatible"
    notes: tuple[str, ...] = ()
    scope: PlanningScope = PlanningScope()

    def __post_init__(self) -> None:
        if self.generation.lower() not in {"v6", "v7", "v8", "v9"}:
            raise ValueError("compatibility generation must be V6, V7, V8, or V9")


PlanningMeshProfile = Profile
PlanningReference = Reference

__all__ = (
    "Assumption",
    "Compatibility",
    "Constraint",
    "Dependency",
    "Evaluation",
    "Objective",
    "Plan",
    "PlanningLifecycle",
    "PlanningMeshProfile",
    "PlanningReference",
    "PlanningScope",
    "Profile",
    "Recommendation",
    "Reference",
    "Resource",
    "Scenario",
    "Schedule",
    "Simulation",
    "SummaryRecord",
    "safe_metadata",
)
