"""Domain contracts for the Enterprise TikTok Performance Insights Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

MAX_RANGE = timedelta(days=366)
MAX_RESULTS = 500


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PerformanceStatus(str, Enum):
    DRAFT = "draft"
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    READY = "ready"
    REVIEW = "review"
    APPROVED = "approved"
    ARCHIVED = "archived"
    DELETED = "deleted"


class PerformanceScope(str, Enum):
    ACCOUNT = "account"
    CONTENT = "content"
    PUBLISHING = "publishing"
    CAMPAIGN = "campaign"
    CREATOR_WORKSPACE = "creator_workspace"
    CONTENT_PIPELINE = "content_pipeline"
    WORKFLOW = "workflow"
    AUTOMATION = "automation"
    EXECUTION = "execution"
    SCHEDULER = "scheduler"
    BROWSER_CLUSTER = "browser_cluster"
    DEVICE_CENTER = "device_center"
    PROXY_CENTER = "proxy_center"
    RESOURCE_CENTER = "resource_center"
    RUNTIME_MANAGER = "runtime_manager"
    RECOVERY_CENTER = "recovery_center"
    RISK_CONTROL = "risk_control"
    GROWTH_CENTER = "growth_center"
    PLATFORM = "platform"


class MetricKind(str, Enum):
    ACCOUNT_HEALTH = "account_health"
    LOGIN_HEALTH = "login_health"
    BROWSER_AVAILABILITY = "browser_availability"
    DEVICE_AVAILABILITY = "device_availability"
    PROXY_AVAILABILITY = "proxy_availability"
    PUBLISHING_SUCCESS_RATE = "publishing_success_rate"
    PUBLISHING_FAILURE_RATE = "publishing_failure_rate"
    PIPELINE_THROUGHPUT = "pipeline_throughput"
    CAMPAIGN_COMPLETION_RATE = "campaign_completion_rate"
    WORKFLOW_SUCCESS_RATE = "workflow_success_rate"
    AUTOMATION_SUCCESS_RATE = "automation_success_rate"
    EXECUTION_SUCCESS_RATE = "execution_success_rate"
    RECOVERY_SUCCESS_RATE = "recovery_success_rate"
    RISK_SCORE = "risk_score"
    RESOURCE_UTILIZATION = "resource_utilization"
    RUNTIME_AVAILABILITY = "runtime_availability"
    QUEUE_WAIT_TIME = "queue_wait_time"
    EXECUTION_TIME = "execution_time"
    REVIEW_TIME = "review_time"
    APPROVAL_TIME = "approval_time"
    GROWTH_TREND = "growth_trend"
    CUSTOM_BOUNDED = "custom_bounded_metric"


class BenchmarkKind(str, Enum):
    HISTORICAL = "historical_baseline"
    WORKSPACE = "workspace_baseline"
    PROFILE = "profile_baseline"
    TARGET = "target_reference"
    PREVIOUS_PERIOD = "previous_period"
    ROLLING_AVERAGE = "rolling_average"
    PERCENTILE = "percentile_reference"


class ComparisonKind(str, Enum):
    CURRENT_PREVIOUS = "current_vs_previous"
    ACTUAL_TARGET = "actual_vs_target"
    ACCOUNT = "account_comparison"
    CAMPAIGN = "campaign_comparison"
    CONTENT = "content_comparison"
    WORKFLOW = "workflow_comparison"
    RESOURCE = "resource_comparison"
    RUNTIME = "runtime_comparison"
    RECOVERY = "recovery_comparison"


class TrendPeriod(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ROLLING_WINDOW = "rolling_window"


class AnomalyKind(str, Enum):
    THRESHOLD = "threshold_anomaly"
    TREND = "trend_anomaly"
    FAILURE_SPIKE = "failure_spike"
    LATENCY_SPIKE = "latency_spike"
    QUEUE_SPIKE = "queue_spike"
    RESOURCE_SPIKE = "resource_spike"
    RISK_SPIKE = "risk_spike"
    RECOVERY_DEGRADATION = "recovery_degradation"
    DATA_QUALITY = "data_quality_anomaly"


class ForecastKind(str, Enum):
    PUBLISHING = "publishing_forecast"
    CAPACITY = "capacity_forecast"
    QUEUE = "queue_forecast"
    RUNTIME = "runtime_forecast"
    FAILURE = "failure_forecast"
    RECOVERY = "recovery_forecast"
    GROWTH = "growth_forecast"
    RISK = "risk_forecast"


class RecommendationKind(str, Enum):
    OPERATIONAL = "operational_recommendation"
    RESOURCE = "resource_recommendation"
    SCHEDULE = "schedule_recommendation"
    WORKFLOW = "workflow_recommendation"
    CONTENT_PLANNING = "content_planning_recommendation"
    CAMPAIGN = "campaign_recommendation"
    RECOVERY = "recovery_recommendation"
    RISK_REDUCTION = "risk_reduction_recommendation"


class ReportKind(str, Enum):
    PERFORMANCE = "performance_overview"
    ACCOUNT = "account_performance"
    CONTENT = "content_performance"
    PUBLISHING = "publishing_performance"
    CAMPAIGN = "campaign_performance"
    WORKFLOW = "workflow_performance"
    AUTOMATION = "automation_performance"
    EXECUTION = "execution_performance"
    RESOURCE = "resource_performance"
    RUNTIME = "runtime_performance"
    RECOVERY = "recovery_performance"
    RISK = "risk_performance"
    GROWTH = "growth_performance"
    CUSTOM_BOUNDED = "custom_bounded_report"


@dataclass(frozen=True, slots=True)
class RequestScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:performance:read"})


@dataclass(frozen=True, slots=True)
class TimeRange:
    start: datetime
    end: datetime

    def validate(self) -> None:
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("Time ranges must be timezone-aware.")
        if self.end <= self.start or self.end - self.start > MAX_RANGE:
            raise ValueError("Time range must be positive and at most 366 days.")


def validate_reference(reference: str, encrypted: bool = False) -> None:
    prefixes = ("encrypted://",) if encrypted else ("ref://", "encrypted://")
    if not reference.startswith(prefixes):
        raise ValueError("Only opaque read-only references are accepted.")


def validate_metadata(metadata: dict[str, Any]) -> None:
    forbidden = {"password", "secret", "token", "cookie", "session", "credential"}
    if forbidden & {str(key).casefold() for key in metadata}:
        raise ValueError("Secrets are forbidden in performance metadata.")


@dataclass(slots=True)
class PerformanceProfile:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    scope: PerformanceScope
    time_range: TimeRange
    status: PerformanceStatus = PerformanceStatus.DRAFT
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all((self.id, self.name, self.tenant, self.workspace, self.owner)):
            raise ValueError("Profile identity and isolation scope are required.")
        self.time_range.validate()
        validate_metadata(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Dataset:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    source_module: str
    source_reference: str
    schema_reference: str
    time_range: TimeRange
    aggregation: str
    freshness_seconds: float
    version: int
    integrity_status: str
    encrypted_reference: str


@dataclass(slots=True)
class Metric:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    kind: MetricKind
    value: float
    unit: str
    dimensions: dict[str, str]
    evidence_references: list[str]
    custom_definition: str = ""


@dataclass(slots=True)
class Benchmark:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    kind: BenchmarkKind
    value: float
    version: int
    reference: str


@dataclass(slots=True)
class Comparison:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    kind: ComparisonKind
    actual: float
    reference_value: float
    delta: float
    evidence_references: list[str]


@dataclass(slots=True)
class Trend:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    period: TrendPeriod
    growth_rate: float
    decline_rate: float
    change_point_reference: str
    confidence: float
    evidence_references: list[str]


@dataclass(slots=True)
class Anomaly:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    kind: AnomalyKind
    severity: str
    explainable_evidence_reference: str
    summary: str


@dataclass(slots=True)
class Forecast:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    kind: ForecastKind
    forecast_window: TimeRange
    projected_value: float
    confidence: float
    evidence_references: list[str]
    advisory: bool = True


@dataclass(slots=True)
class Insight:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    summary: str
    finding: str
    affected_scope: PerformanceScope
    severity: str
    confidence: float
    evidence_references: list[str]
    comparison_reference: str = ""
    trend_reference: str = ""
    anomaly_reference: str = ""
    forecast_reference: str = ""
    recommended_review: str = ""


@dataclass(slots=True)
class Recommendation:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    kind: RecommendationKind
    title: str
    rationale: str
    evidence_references: list[str]
    optimization_handoff_reference: str = ""
    decision_handoff_reference: str = ""
    approved: bool = False


@dataclass(slots=True)
class Report:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    kind: ReportKind
    title: str
    content_reference: str
    custom_definition: str = ""


@dataclass(slots=True)
class Snapshot:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    kind: str
    values: dict[str, float]
    timestamp: datetime
    version: int
    integrity_valid: bool


@dataclass(slots=True)
class AuditEvent:
    tenant: str
    workspace: str
    actor: str
    action: str
    entity_reference: str
    timestamp: datetime = field(default_factory=utcnow)
