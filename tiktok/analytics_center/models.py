"""Domain contracts for the enterprise TikTok AI Analytics Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AnalyticsStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ReportType(str, Enum):
    ACCOUNTS = "accounts"
    BROWSERS = "browsers"
    PROXIES = "proxies"
    PUBLISHING = "publishing"
    CONTENT = "content"
    COLLECTION = "collection"
    INTERACTION = "interaction"
    RISK = "risk"
    WORKFLOW = "workflow"
    OPERATIONS = "operations"
    CUSTOM = "custom"


class KPIKind(str, Enum):
    ACCOUNT_HEALTH = "account_health"
    PUBLISHING_SUCCESS = "publishing_success"
    WORKFLOW_SUCCESS = "workflow_success"
    INTERACTION_SUCCESS = "interaction_success"
    COLLECTION_SUCCESS = "collection_success"
    PROXY_AVAILABILITY = "proxy_availability"
    BROWSER_AVAILABILITY = "browser_availability"
    RISK_SCORE = "risk_score"
    RECOVERY_SUCCESS = "recovery_success"
    EXECUTION_TIME = "execution_time"


class Period(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom_range"


class ExportFormat(str, Enum):
    CSV = "csv"
    JSON = "json"
    XLSX_REFERENCE = "xlsx_reference"
    PDF_REFERENCE = "pdf_reference"


@dataclass(frozen=True, slots=True)
class AnalyticsScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:analytics:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


def validate_safe_mapping(value: dict[str, Any]) -> None:
    forbidden = {"password", "secret", "token", "cookie", "credential", "session"}
    if forbidden & {key.casefold() for key in value}:
        raise ValueError("Secrets are forbidden in analytics records.")


@dataclass(slots=True)
class AnalyticsWorkspace:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    status: AnalyticsStatus = AnalyticsStatus.DRAFT
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not all((self.id, self.name, self.tenant, self.workspace, self.owner)):
            raise ValueError("Analytics workspace identity and scope are required.")
        if self.version < 1:
            raise ValueError("Version must be positive.")
        validate_safe_mapping(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class DataPoint:
    timestamp: datetime
    value: float


@dataclass(slots=True)
class Report:
    id: str
    tenant: str
    workspace: str
    name: str
    report_type: ReportType
    dataset_reference: str
    owner: str
    status: AnalyticsStatus = AnalyticsStatus.DRAFT
    custom_report_reference: str = ""
    generated_at: datetime | None = None


@dataclass(slots=True)
class KPI:
    id: str
    tenant: str
    workspace: str
    kind: KPIKind
    value: float
    unit: str
    evidence_references: list[str] = field(default_factory=list)
    measured_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class Trend:
    id: str
    tenant: str
    workspace: str
    metric: str
    period: Period
    points: list[DataPoint]
    comparison: float = 0
    growth: float = 0
    regression: bool = False


@dataclass(slots=True)
class Forecast:
    id: str
    tenant: str
    workspace: str
    metric: str
    forecast_window: int
    historical_projection: list[DataPoint]
    capacity_trend: float
    failure_trend: float
    health_trend: float
    confidence: float


@dataclass(slots=True)
class HistorySnapshot:
    id: str
    tenant: str
    workspace: str
    metrics: dict[str, float]
    retention_days: int = 365
    archived: bool = False
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class Insight:
    id: str
    tenant: str
    workspace: str
    anomaly_detection_reference: str
    trend_summary: str
    recommendations: list[str]
    operational_highlights: list[str]
    evidence_references: list[str]
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class ExportRecord:
    id: str
    tenant: str
    workspace: str
    report_reference: str
    format: ExportFormat
    artifact_reference: str
    requested_by: str
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class AuditRecord:
    actor: str
    action: str
    resource: str
    tenant: str
    workspace: str
    detail: str
    timestamp: datetime = field(default_factory=utcnow)
