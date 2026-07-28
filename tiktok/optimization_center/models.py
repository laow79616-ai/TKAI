"""Domain contracts for the Enterprise TikTok AI Continuous Optimization Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OptimizationStatus(str, Enum):
    DRAFT = "draft"
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    PROPOSED = "proposed"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    APPLYING = "applying"
    VALIDATING = "validating"
    COMPLETED = "completed"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class OptimizationScope(str, Enum):
    RUNTIME = "runtime"
    BROWSER_CLUSTER = "browser_cluster"
    DEVICE_CENTER = "device_center"
    PROXY_CENTER = "proxy_center"
    TASK_SCHEDULER = "task_scheduler"
    RESOURCE_CENTER = "resource_center"
    WORKFLOW_CENTER = "workflow_center"
    AUTOMATION_ENGINE = "automation_engine"
    EXECUTION_ENGINE = "execution_engine"
    RECOVERY_CENTER = "recovery_center"
    PUBLISHING_CENTER = "publishing_center"
    COLLECTION_CENTER = "collection_center"
    INTERACTION_CENTER = "interaction_center"
    RISK_CONTROL_CENTER = "risk_control_center"
    ANALYTICS_CENTER = "analytics_center"
    LOCAL_RUNTIME = "local_runtime"


class ObjectiveKind(str, Enum):
    RELIABILITY = "reliability"
    AVAILABILITY = "availability"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    RESOURCE_EFFICIENCY = "resource_efficiency"
    QUEUE_EFFICIENCY = "queue_efficiency"
    RECOVERY_SUCCESS = "recovery_success"
    STARTUP_TIME = "startup_time"
    SHUTDOWN_TIME = "shutdown_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    STORAGE_USAGE = "storage_usage"
    BROWSER_UTILIZATION = "browser_utilization"
    DEVICE_UTILIZATION = "device_utilization"
    PROXY_UTILIZATION = "proxy_utilization"
    WORKER_UTILIZATION = "worker_utilization"
    CUSTOM_BOUNDED = "custom_bounded"


class CandidateKind(str, Enum):
    CONCURRENCY = "concurrency_adjustment"
    QUEUE_LIMIT = "queue_limit_adjustment"
    WORKER_CAPACITY = "worker_capacity_adjustment"
    BROWSER_POOL = "browser_pool_adjustment"
    DEVICE_ALLOCATION = "device_allocation_adjustment"
    PROXY_ALLOCATION = "proxy_allocation_adjustment"
    SCHEDULE = "schedule_adjustment"
    RETRY = "retry_adjustment"
    BACKOFF = "backoff_adjustment"
    TIMEOUT = "timeout_adjustment"
    COOLDOWN = "cooldown_adjustment"
    RESOURCE_QUOTA = "resource_quota_adjustment"
    RECOVERY_POLICY = "recovery_policy_adjustment"
    WORKFLOW_PARAMETER = "workflow_parameter_adjustment"


class ExperimentKind(str, Enum):
    DRY_RUN = "dry_run"
    SIMULATION = "simulation"
    SHADOW = "shadow_evaluation"
    CANARY = "canary_configuration"
    AB_COMPARISON = "ab_comparison"
    HISTORICAL_REPLAY = "historical_replay"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class RequestScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:optimization:read"})


def validate_metadata(value: dict[str, Any]) -> None:
    forbidden = {"password", "secret", "token", "cookie", "credential", "session"}
    if forbidden & {key.casefold() for key in value}:
        raise ValueError("Secrets are forbidden in optimization metadata.")


@dataclass(slots=True)
class OptimizationProfile:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    scope: OptimizationScope
    priority: int = 50
    status: OptimizationStatus = OptimizationStatus.DRAFT
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all((self.id, self.name, self.tenant, self.workspace, self.owner)):
            raise ValueError("Profile identity and isolation scope are required.")
        if not 1 <= self.priority <= 100:
            raise ValueError("Priority must be within [1, 100].")
        validate_metadata(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["scope"] = self.scope.value
        result["status"] = self.status.value
        return result


@dataclass(slots=True)
class Objective:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    kind: ObjectiveKind
    target: float
    unit: str
    weight: float = 1.0
    minimum: float | None = None
    maximum: float | None = None


@dataclass(slots=True)
class Baseline:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    version: int
    configuration_reference: str
    limits: dict[str, float]
    metrics: dict[str, float]
    health: str
    captured_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class Signal:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    kind: str
    value: float
    evidence_references: list[str]
    observed_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class CandidateChange:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    kind: CandidateKind
    target_module: OptimizationScope
    parameter: str
    current_value: float
    proposed_value: float
    expected_version: int
    evidence_references: list[str]
    maximum_change_percentage: float = 20.0

    def validate(self) -> None:
        if self.current_value == 0:
            raise ValueError("A zero baseline cannot produce a bounded percentage.")
        percentage = (
            abs(self.proposed_value - self.current_value)
            / abs(self.current_value)
            * 100
        )
        if not 0 < self.maximum_change_percentage <= 25:
            raise ValueError("Maximum change percentage must be within (0, 25].")
        if percentage > self.maximum_change_percentage:
            raise ValueError("Candidate exceeds the bounded maximum change percentage.")
        unsafe = ("captcha", "bypass", "circumvent", "anti-detection", "spam", "mass")
        if any(term in self.parameter.casefold() for term in unsafe):
            raise ValueError("Unsafe optimization parameters are forbidden.")


@dataclass(slots=True)
class Experiment:
    id: str
    candidate_id: str
    tenant: str
    workspace: str
    kind: ExperimentKind
    result_reference: str
    expected_improvement: float
    observed_improvement: float
    regression_detected: bool


@dataclass(slots=True)
class Evaluation:
    id: str
    candidate_id: str
    tenant: str
    workspace: str
    expected_improvement: float
    observed_improvement: float
    risk_level: RiskLevel
    confidence: float
    evidence_references: list[str]
    rollback_criteria: str


@dataclass(slots=True)
class Recommendation:
    id: str
    candidate_id: str
    tenant: str
    workspace: str
    target_module: OptimizationScope
    current_value: float
    proposed_value: float
    expected_benefit: str
    risk_level: RiskLevel
    confidence: float
    evidence_references: list[str]
    validation_plan: str
    rollback_plan: str
    approved: bool = False


@dataclass(slots=True)
class Approval:
    id: str
    recommendation_id: str
    tenant: str
    workspace: str
    reviewer: str
    notes: str
    approved: bool
    expires_at: datetime
    rejection_reason: str = ""
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class ChangeRecord:
    id: str
    recommendation_id: str
    tenant: str
    workspace: str
    target_configuration_reference: str
    expected_version: int
    backup_reference: str
    checkpoint_reference: str
    result_reference: str = ""
    validation_window_seconds: int = 300
    applied_at: datetime | None = None


@dataclass(slots=True)
class ValidationResult:
    id: str
    change_id: str
    tenant: str
    workspace: str
    health: str
    performance_delta: float
    resource_delta: float
    failure_rate_delta: float
    recovery_rate_delta: float
    risk_state: str
    regression_detected: bool
    accepted: bool


@dataclass(slots=True)
class RollbackRecord:
    id: str
    change_id: str
    tenant: str
    workspace: str
    reason: str
    result_reference: str
    automatic: bool
    verified: bool
    rolled_back_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class AuditEvent:
    profile_id: str
    tenant: str
    workspace: str
    actor: str
    action: str
    detail: str = ""
    timestamp: datetime = field(default_factory=utcnow)
