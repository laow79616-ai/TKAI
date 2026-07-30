"""Immutable contracts for the bounded V8 Hyper Simulation & Forecasting Fabric."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def immutable_metadata(
    value: Mapping[str, object] | None = None,
) -> Mapping[str, object]:
    return MappingProxyType(dict(value or {}))


PROHIBITED_KEYS = frozenset(
    {
        "execute",
        "execution",
        "runtime_mutation",
        "tiktok_action",
        "browser_action",
        "account_action",
        "allocate",
        "resource_allocation",
        "scheduler_mutation",
        "automatic_approval",
        "password",
        "cookie",
        "session",
        "proxy_credentials",
        "api_key",
    }
)


def validate_safe_metadata(value: Mapping[str, object]) -> None:
    for key, item in value.items():
        normalized = str(key).lower()
        if normalized in PROHIBITED_KEYS:
            raise ValueError(f"unsafe or active metadata is prohibited: {key}")
        if isinstance(item, Mapping):
            validate_safe_metadata(item)


class SimulationLifecycle(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    COLLECTING_INPUTS = "collecting-inputs"
    VALIDATING = "validating"
    READY = "ready"
    SIMULATING = "simulating"
    EVALUATING = "evaluating"
    UNDER_REVIEW = "under-review"
    APPROVED_REFERENCE = "approved-reference"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ModelKind(str, Enum):
    DETERMINISTIC = "deterministic"
    RULE_BASED = "rule-based"
    TREND = "trend"
    CAPACITY = "capacity"
    SCHEDULE = "schedule"
    DEPENDENCY = "dependency"
    RISK = "risk"
    RECOVERY = "recovery"
    SCENARIO = "scenario"
    MOCK = "mock"
    TEST = "test"


class ScenarioKind(str, Enum):
    BASELINE = "baseline"
    CONSERVATIVE = "conservative"
    EXPECTED = "expected"
    GROWTH = "growth"
    CAPACITY_CONSTRAINED = "capacity-constrained"
    RESOURCE_CONSTRAINED = "resource-constrained"
    SCHEDULE_CONSTRAINED = "schedule-constrained"
    RISK_CONSTRAINED = "risk-constrained"
    RECOVERY = "recovery"
    DEGRADED_RUNTIME = "degraded-runtime"
    RESTRICTED_ACCOUNT = "restricted-account"
    WORKSPACE_PAUSED = "workspace-paused"
    KILL_SWITCH_ACTIVE = "kill-switch-active"
    MAINTENANCE = "maintenance"
    COMPATIBILITY_DEGRADED = "compatibility-degraded"


class TrendKind(str, Enum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"
    SEASONAL = "seasonal"
    ANOMALOUS = "anomalous"
    INSUFFICIENT_EVIDENCE = "insufficient-evidence"
    UNKNOWN = "unknown"


class DependencyKind(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    DATA = "data"
    APPROVAL = "approval"
    GOVERNANCE = "governance"
    RESOURCE = "resource"
    SCHEDULE = "schedule"
    RECOVERY = "recovery"
    COMPATIBILITY = "compatibility"


class ConstraintKind(str, Enum):
    GOVERNANCE = "governance"
    SECURITY = "security"
    RUNTIME = "runtime"
    PLATFORM_RESTRICTION = "platform-restriction"
    ACCOUNT = "account"
    WORKSPACE = "workspace"
    PAUSE = "pause"
    KILL_SWITCH = "kill-switch"
    RESOURCE = "resource"
    SCHEDULE = "schedule"
    DEPENDENCY = "dependency"
    RISK = "risk"
    RECOVERY = "recovery"
    COMPATIBILITY = "compatibility"
    TIME_HORIZON = "time-horizon"
    RESULT_SIZE = "result-size"


@dataclass(frozen=True)
class SimulationScope:
    tenant: str = "default"
    workspace: str = "default"
    namespace: str = "default"
    profile: str = "*"


@dataclass(frozen=True)
class SimulationReference:
    identifier: str
    version: str = ""
    generation: str = "v8"
    framework: str = ""
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.identifier or any(char.isspace() for char in self.identifier):
            raise ValueError("reference identifier must be non-empty without spaces")
        if self.generation not in {"v6", "v7", "v8"}:
            raise ValueError("reference generation must be v6, v7, or v8")
        validate_safe_metadata(self.metadata)
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class VersionMetadata:
    version: str = "1.0.0"
    effective_date: datetime = field(default_factory=utc_now)
    superseded_by: SimulationReference | None = None
    change_reason: str = ""
    change_history: tuple[Mapping[str, object], ...] = ()
    deprecation_metadata: Mapping[str, object] = field(
        default_factory=immutable_metadata
    )


@dataclass(frozen=True)
class SimulationProfile:
    profile_id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    owner: str = ""
    namespace: str = "default"
    tenant_reference: str = "default"
    workspace_reference: str = "default"
    scope: SimulationScope = SimulationScope()
    time_horizon: int = 1
    model_references: tuple[SimulationReference, ...] = ()
    input_references: tuple[SimulationReference, ...] = ()
    baseline_references: tuple[SimulationReference, ...] = ()
    scenario_references: tuple[SimulationReference, ...] = ()
    forecast_references: tuple[SimulationReference, ...] = ()
    constraint_references: tuple[SimulationReference, ...] = ()
    governance_references: tuple[SimulationReference, ...] = ()
    compatibility_references: tuple[SimulationReference, ...] = ()
    lifecycle: SimulationLifecycle = SimulationLifecycle.DRAFT
    health: str = "unknown"
    metrics: Mapping[str, object] = field(default_factory=immutable_metadata)
    audit: tuple[Mapping[str, object], ...] = ()
    tags: tuple[str, ...] = ()
    safe_metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.profile_id or not self.name:
            raise ValueError("profile_id and name are required")
        if self.time_horizon < 1:
            raise ValueError("time_horizon must be positive")
        validate_safe_metadata(self.safe_metadata)
        object.__setattr__(self, "metrics", immutable_metadata(self.metrics))
        object.__setattr__(
            self, "safe_metadata", immutable_metadata(self.safe_metadata)
        )
        object.__setattr__(
            self, "audit", tuple(immutable_metadata(x) for x in self.audit)
        )

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True)
class InputMetadata:
    input_id: str
    source_reference: SimulationReference
    input_type: str
    subject_reference: SimulationReference
    time_range: str = ""
    value_reference: SimulationReference | None = None
    unit_metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    version: str = "1.0.0"
    integrity_status: str = "unknown"
    freshness: float = 0.0
    reliability: float = 0.0
    confidence: float = 0.0
    audit_reference: SimulationReference | None = None
    safe_metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: SimulationScope = SimulationScope()

    def __post_init__(self) -> None:
        if self.value_reference is None:
            raise ValueError("sensitive input values must remain reference-only")
        for value in (self.freshness, self.reliability, self.confidence):
            if not 0.0 <= value <= 1.0:
                raise ValueError("quality values must be between zero and one")
        validate_safe_metadata(self.safe_metadata)
        object.__setattr__(
            self, "unit_metadata", immutable_metadata(self.unit_metadata)
        )
        object.__setattr__(
            self, "safe_metadata", immutable_metadata(self.safe_metadata)
        )


@dataclass(frozen=True)
class BaselineMetadata:
    baseline_id: str
    baseline_type: str
    source_reference: SimulationReference
    version: str = "1.0.0"
    time_range: str = ""
    integrity_status: str = "unknown"
    confidence: float = 0.0
    scope: SimulationScope = SimulationScope()


@dataclass(frozen=True)
class ModelMetadata:
    model_id: str
    kind: ModelKind
    version: str = "1.0.0"
    algorithm: str = "bounded-deterministic"
    parameter_metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    limitations: tuple[str, ...] = ()
    scope: SimulationScope = SimulationScope()

    def __post_init__(self) -> None:
        if self.algorithm not in {
            "bounded-deterministic",
            "rule-table",
            "linear-trend",
        }:
            raise ValueError("arbitrary model execution is prohibited")
        validate_safe_metadata(self.parameter_metadata)
        object.__setattr__(
            self, "parameter_metadata", immutable_metadata(self.parameter_metadata)
        )


@dataclass(frozen=True)
class ScenarioMetadata:
    scenario_id: str
    kind: ScenarioKind
    name: str
    assumption_references: tuple[SimulationReference, ...] = ()
    constraint_references: tuple[SimulationReference, ...] = ()
    safe_metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: SimulationScope = SimulationScope()


@dataclass(frozen=True)
class SimulationMetadata:
    simulation_id: str
    profile_reference: SimulationReference
    scenario_reference: SimulationReference
    model_reference: SimulationReference
    simulation_types: tuple[str, ...] = ()
    result_reference: SimulationReference | None = None
    deterministic: bool = True
    limitations: tuple[str, ...] = ()
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=utc_now)
    scope: SimulationScope = SimulationScope()

    @property
    def offline_only(self) -> bool:
        return True


@dataclass(frozen=True)
class ForecastMetadata:
    forecast_id: str
    profile_reference: SimulationReference
    subject_reference: SimulationReference
    forecast_type: str
    horizon: int
    baseline_reference: SimulationReference
    scenario_reference: SimulationReference
    model_reference: SimulationReference
    estimate_reference: SimulationReference
    confidence_range_metadata: Mapping[str, object] = field(
        default_factory=immutable_metadata
    )
    assumption_references: tuple[SimulationReference, ...] = ()
    constraint_references: tuple[SimulationReference, ...] = ()
    risk_references: tuple[SimulationReference, ...] = ()
    uncertainty_references: tuple[SimulationReference, ...] = ()
    evaluation_reference: SimulationReference | None = None
    limitations: tuple[str, ...] = ()
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=utc_now)
    scope: SimulationScope = SimulationScope()

    def __post_init__(self) -> None:
        if self.horizon < 1 or not self.limitations or not self.uncertainty_references:
            raise ValueError(
                "forecast requires bounded horizon, uncertainty, and limitations"
            )
        object.__setattr__(
            self,
            "confidence_range_metadata",
            immutable_metadata(self.confidence_range_metadata),
        )

    @property
    def advisory(self) -> bool:
        return True


@dataclass(frozen=True)
class TrendMetadata:
    trend_id: str
    kind: TrendKind
    subject_reference: SimulationReference
    evidence_references: tuple[SimulationReference, ...] = ()
    limitations: tuple[str, ...] = ()
    causal_claim: bool = False
    scope: SimulationScope = SimulationScope()

    def __post_init__(self) -> None:
        if self.causal_claim:
            raise ValueError("unsupported causal claims are prohibited")


@dataclass(frozen=True)
class CapacityForecastMetadata:
    capacity_id: str
    capacity_type: str
    estimated_capacity: float
    estimated_demand: float
    confidence: float
    limitations: tuple[str, ...]
    scope: SimulationScope = SimulationScope()

    @property
    def allocated(self) -> bool:
        return False


@dataclass(frozen=True)
class ResourceForecastMetadata:
    resource_id: str
    estimated_demand: float
    estimated_availability: float
    estimated_utilization: float
    estimated_shortfall: float = 0.0
    estimated_surplus: float = 0.0
    reservation_reference: SimulationReference | None = None
    constraint_reference: SimulationReference | None = None
    confidence: float = 0.0
    limitations: tuple[str, ...] = ()
    scope: SimulationScope = SimulationScope()

    @property
    def allocated(self) -> bool:
        return False


@dataclass(frozen=True)
class ScheduleForecastMetadata:
    schedule_id: str
    earliest_start: str
    latest_finish: str
    estimated_duration: str
    windows: Mapping[str, object] = field(default_factory=immutable_metadata)
    confidence: float = 0.0
    limitations: tuple[str, ...] = ()
    scope: SimulationScope = SimulationScope()

    @property
    def scheduler_mutated(self) -> bool:
        return False


@dataclass(frozen=True)
class DependencyMetadata:
    dependency_id: str
    kind: DependencyKind
    source: SimulationReference
    target: SimulationReference
    available: bool = True
    scope: SimulationScope = SimulationScope()


@dataclass(frozen=True)
class RiskForecastMetadata:
    risk_id: str
    probability: float
    impact: float
    severity: str
    trend: TrendKind
    horizon: int
    mitigation_reference: SimulationReference | None = None
    recovery_reference: SimulationReference | None = None
    governance_review_required: bool = False
    residual_risk: float = 0.0
    confidence: float = 0.0
    limitations: tuple[str, ...] = ()
    scope: SimulationScope = SimulationScope()


@dataclass(frozen=True)
class UncertaintyMetadata:
    uncertainty_id: str
    uncertainty_type: str
    magnitude: float
    explanation: str
    limitations: tuple[str, ...] = ()
    scope: SimulationScope = SimulationScope()


@dataclass(frozen=True)
class ConfidenceMetadata:
    confidence_id: str
    original_confidence: float
    evidence_adjusted_confidence: float
    baseline_adjusted_confidence: float
    scenario_adjusted_confidence: float
    model_adjusted_confidence: float
    risk_adjusted_confidence: float
    calibrated_confidence: float
    confidence_range_metadata: Mapping[str, object] = field(
        default_factory=immutable_metadata
    )
    historical_accuracy_reference: SimulationReference | None = None
    calibration_explanation: str = ""
    limitations: tuple[str, ...] = ()
    scope: SimulationScope = SimulationScope()


@dataclass(frozen=True)
class AssumptionMetadata:
    assumption_id: str
    description: str
    source_reference: SimulationReference
    evidence_reference: SimulationReference | None = None
    confidence: float = 0.0
    expiry: datetime | None = None
    validation_status: str = "unvalidated"
    risk_if_incorrect: str = ""
    owner: str = ""
    version: str = "1.0.0"
    scope: SimulationScope = SimulationScope()

    @property
    def is_fact(self) -> bool:
        return False


@dataclass(frozen=True)
class ConstraintMetadata:
    constraint_id: str
    kind: ConstraintKind
    description: str
    limit: int | float | None = None
    scope: SimulationScope = SimulationScope()


@dataclass(frozen=True)
class ComparisonMetadata:
    comparison_id: str
    comparison_type: str
    left_reference: SimulationReference
    right_reference: SimulationReference
    findings: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    scope: SimulationScope = SimulationScope()


@dataclass(frozen=True)
class EvaluationMetadata:
    evaluation_id: str
    evaluation_type: str
    subject_reference: SimulationReference
    score: float
    factors: tuple[Mapping[str, object], ...]
    weight_metadata: Mapping[str, object]
    supporting_references: tuple[SimulationReference, ...]
    limitations: tuple[str, ...]
    explanation_summary: str
    scope: SimulationScope = SimulationScope()

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 1:
            raise ValueError("evaluation score must be between zero and one")
        if not self.factors or not self.explanation_summary:
            raise ValueError("scores must be explainable")


@dataclass(frozen=True)
class RecommendationMetadata:
    recommendation_id: str
    recommendation_type: str
    summary: str
    supporting_references: tuple[SimulationReference, ...] = ()
    limitations: tuple[str, ...] = ()
    scope: SimulationScope = SimulationScope()

    @property
    def advisory(self) -> bool:
        return True

    @property
    def executable(self) -> bool:
        return False


@dataclass(frozen=True)
class ReviewMetadata:
    review_id: str
    reviewer: str
    review_type: str
    review_scope: str
    findings: tuple[str, ...] = ()
    required_changes: tuple[str, ...] = ()
    advisory_recommendations: tuple[str, ...] = ()
    status: str = "pending"
    timestamp: datetime = field(default_factory=utc_now)
    audit_reference: SimulationReference | None = None
    scope: SimulationScope = SimulationScope()


@dataclass(frozen=True)
class GovernanceMetadata:
    governance_id: str
    policy_references: tuple[SimulationReference, ...] = ()
    governance_constraints: tuple[SimulationReference, ...] = ()
    review_requirements: tuple[str, ...] = ()
    approval_requirements: tuple[str, ...] = ()
    risk_thresholds: Mapping[str, object] = field(default_factory=immutable_metadata)
    pause_aware: bool = True
    kill_switch_aware: bool = True
    audit_requirements: tuple[str, ...] = ()
    scope: SimulationScope = SimulationScope()


@dataclass(frozen=True)
class CompatibilityMetadata:
    compatibility_id: str
    generation: str
    source_reference: SimulationReference
    status: str = "compatible"
    preserved_behaviors: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    scope: SimulationScope = SimulationScope()

    def __post_init__(self) -> None:
        if self.generation not in {"v6", "v7", "v8"}:
            raise ValueError("compatibility generation must be v6, v7, or v8")


Reference = SimulationReference
PlanningLifecycle = SimulationLifecycle
PlanningScope = SimulationScope
PlanningReference = SimulationReference
PlanningProfile = SimulationProfile
