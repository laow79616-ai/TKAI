"""Secure, tenant-scoped Enterprise AI Business Intelligence control plane."""

from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol, TypeVar

from .metrics import BusinessIntelligenceMetrics


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WorkspaceStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Visibility(str, Enum):
    PRIVATE = "private"
    WORKSPACE = "workspace"
    TENANT = "tenant"


class DataSourceType(str, Enum):
    DATABASE = "database"
    WAREHOUSE = "warehouse"
    LAKEHOUSE = "lakehouse"
    API = "api"
    FILE = "file"
    EVENT_STREAM = "event_stream"


class DimensionType(str, Enum):
    CATEGORICAL = "categorical"
    TEMPORAL = "temporal"
    GEOGRAPHIC = "geographic"
    ORGANIZATIONAL = "organizational"
    CUSTOM = "custom"


class Aggregation(str, Enum):
    SUM = "sum"
    AVERAGE = "average"
    MINIMUM = "minimum"
    MAXIMUM = "maximum"
    COUNT = "count"
    DISTINCT_COUNT = "distinct_count"
    RATIO = "ratio"
    PERCENTAGE = "percentage"
    CUSTOM = "custom"


class VisualizationType(str, Enum):
    TABLE = "table"
    KPI = "kpi"
    LINE = "line_chart"
    BAR = "bar_chart"
    AREA = "area_chart"
    PIE = "pie_chart"
    SCATTER = "scatter_plot"
    HEATMAP = "heatmap"
    FUNNEL = "funnel"
    MAP = "map"
    CUSTOM = "custom"


class ExportFormat(str, Enum):
    CSV = "csv"
    JSON = "json"
    PDF = "pdf"
    SPREADSHEET = "spreadsheet"
    IMAGE = "image"


class Scoped(Protocol):
    id: str
    tenant: str
    workspace: str


ScopedT = TypeVar("ScopedT", bound=Scoped)


@dataclass(frozen=True, slots=True)
class BIScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"business_intelligence:read"})

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class BIWorkspace:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    status: WorkspaceStatus = WorkspaceStatus.DRAFT
    visibility: Visibility = Visibility.PRIVATE
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DataSource:
    id: str
    tenant: str
    workspace: str
    name: str
    type: DataSourceType
    reference: str
    credential_reference: str | None = None
    health: str = "unknown"
    refresh_policy: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Dataset:
    id: str
    tenant: str
    workspace: str
    name: str
    data_source_id: str
    schema: dict[str, Any]
    fields: tuple[str, ...] = ()
    types: dict[str, str] = field(default_factory=dict)
    relationships: tuple[dict[str, Any], ...] = ()
    calculated_fields: dict[str, str] = field(default_factory=dict)
    refresh_status: str = "pending"
    version: str = "1"
    lineage_reference: str | None = None


@dataclass(slots=True)
class Metric:
    id: str
    tenant: str
    workspace: str
    name: str
    description: str
    formula: str
    aggregation: Aggregation
    unit: str
    owner: str
    target: float | None = None
    threshold: float | None = None
    version: str = "1"


@dataclass(slots=True)
class Dimension:
    id: str
    tenant: str
    workspace: str
    name: str
    type: DimensionType
    hierarchy: tuple[str, ...] = ()
    filters: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Measure:
    id: str
    tenant: str
    workspace: str
    name: str
    aggregation: Aggregation
    expression: str


@dataclass(slots=True)
class SemanticModel:
    id: str
    tenant: str
    workspace: str
    name: str
    dataset_ids: tuple[str, ...]
    business_entities: tuple[str, ...] = ()
    metric_ids: tuple[str, ...] = ()
    dimension_ids: tuple[str, ...] = ()
    measure_ids: tuple[str, ...] = ()
    relationships: tuple[dict[str, Any], ...] = ()
    hierarchies: tuple[dict[str, Any], ...] = ()
    time_intelligence: dict[str, Any] = field(default_factory=dict)
    business_definitions: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class BIQuery:
    id: str
    tenant: str
    workspace: str
    dataset_id: str
    metrics: tuple[str, ...] = ()
    dimensions: tuple[str, ...] = ()
    filters: dict[str, Any] = field(default_factory=dict)
    sorting: tuple[str, ...] = ()
    page: int = 1
    page_size: int = 100
    time_range: tuple[str, str] | None = None
    row_limit: int = 10_000
    timeout_seconds: int = 30


@dataclass(slots=True)
class Report:
    id: str
    tenant: str
    workspace: str
    title: str
    description: str = ""
    sections: tuple[dict[str, Any], ...] = ()
    visualizations: tuple[str, ...] = ()
    filters: dict[str, Any] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    schedule: str | None = None
    export: dict[str, Any] = field(default_factory=dict)
    permissions: tuple[str, ...] = ()


@dataclass(slots=True)
class Dashboard:
    id: str
    tenant: str
    workspace: str
    name: str
    widgets: tuple[dict[str, Any], ...] = ()
    layouts: dict[str, Any] = field(default_factory=dict)
    global_filters: dict[str, Any] = field(default_factory=dict)
    drill_down: bool = True
    cross_filtering: bool = True
    refresh_seconds: int = 300
    sharing: dict[str, Any] = field(default_factory=dict)
    version: str = "1"


@dataclass(slots=True)
class Visualization:
    id: str
    tenant: str
    workspace: str
    name: str
    type: VisualizationType
    query_id: str
    configuration: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Insight:
    id: str
    tenant: str
    workspace: str
    kind: str
    narrative_summary: str
    supporting_evidence_reference: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Alert:
    id: str
    tenant: str
    workspace: str
    metric_id: str
    kind: str
    recipients: tuple[str, ...]
    threshold: float | None = None
    schedule: str | None = None
    channels: tuple[str, ...] = ()
    cooldown_seconds: int = 300
    acknowledged: bool = False
    status: str = "active"


@dataclass(slots=True)
class Subscription:
    id: str
    tenant: str
    workspace: str
    resource_type: str
    resource_id: str
    schedule: str
    format: ExportFormat
    recipients: tuple[str, ...]
    delivery_history: tuple[dict[str, Any], ...] = ()
    retry_limit: int = 3


@dataclass(slots=True)
class ExportRequest:
    id: str
    tenant: str
    workspace: str
    resource_type: str
    resource_id: str
    format: ExportFormat
    row_limit: int = 100_000
    size_limit_bytes: int = 50_000_000
    status: str = "pending"


@dataclass(slots=True)
class GovernancePolicy:
    id: str
    tenant: str
    workspace: str
    owner: str
    certification: str
    glossary_reference: str | None = None
    lineage: dict[str, Any] = field(default_factory=dict)
    classification: str = "internal"
    access_policy: dict[str, Any] = field(default_factory=dict)
    retention_days: int = 365


@dataclass(frozen=True, slots=True)
class AuditEntry:
    action: str
    actor: str
    tenant: str
    workspace: str
    occurred_at: datetime
    metadata: dict[str, Any]


class BusinessIntelligencePlatform:
    TRANSITIONS = {
        WorkspaceStatus.DRAFT: {WorkspaceStatus.ACTIVE, WorkspaceStatus.ARCHIVED},
        WorkspaceStatus.ACTIVE: {WorkspaceStatus.PAUSED, WorkspaceStatus.ARCHIVED},
        WorkspaceStatus.PAUSED: {WorkspaceStatus.ACTIVE, WorkspaceStatus.ARCHIVED},
        WorkspaceStatus.ARCHIVED: {WorkspaceStatus.DELETED},
        WorkspaceStatus.DELETED: set(),
    }
    SECRET_KEYS = re.compile(
        r"(?:password|passwd|secret|token|api[_-]?key|authorization)", re.I
    )
    SAFE_EXPRESSION = re.compile(r"^[A-Za-z0-9_ .,+*/%()<>!=:-]+$")
    CREDENTIAL_REFERENCE = re.compile(
        r"^(?:vault|secret|credential|kms)://[A-Za-z0-9_./:@-]+$"
    )

    def __init__(self, *, max_rows: int = 100_000, max_timeout: int = 120) -> None:
        self.max_rows = max_rows
        self.max_timeout = max_timeout
        self.workspaces: dict[str, BIWorkspace] = {}
        self.data_sources: dict[str, DataSource] = {}
        self.datasets: dict[str, Dataset] = {}
        self.semantic_models: dict[str, SemanticModel] = {}
        self.metrics_definitions: dict[str, Metric] = {}
        self.dimensions: dict[str, Dimension] = {}
        self.measures: dict[str, Measure] = {}
        self.queries: dict[str, BIQuery] = {}
        self.reports: dict[str, Report] = {}
        self.dashboards: dict[str, Dashboard] = {}
        self.visualizations: dict[str, Visualization] = {}
        self.insights: dict[str, Insight] = {}
        self.alerts: dict[str, Alert] = {}
        self.subscriptions: dict[str, Subscription] = {}
        self.exports: dict[str, ExportRequest] = {}
        self.governance: dict[str, GovernancePolicy] = {}
        self.audit: list[AuditEntry] = []
        self.metrics = BusinessIntelligenceMetrics()

    @staticmethod
    def _in_scope(record: Any, scope: BIScope) -> bool:
        return bool(
            record.tenant == scope.tenant and record.workspace == scope.workspace
        )

    @staticmethod
    def _require(scope: BIScope, permission: str) -> None:
        if (
            permission not in scope.permissions
            and "business_intelligence:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    def _get(
        self, records: dict[str, ScopedT], record_id: str, scope: BIScope
    ) -> ScopedT:
        record = records[record_id]
        if not self._in_scope(record, scope):
            raise PermissionError("Cross-tenant or cross-workspace access denied.")
        return record

    def _validate_safe(self, value: Any) -> None:
        if isinstance(value, dict):
            if any(self.SECRET_KEYS.search(str(key)) for key in value):
                raise ValueError("Secrets and plaintext credentials are not allowed.")
            for item in value.values():
                self._validate_safe(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                self._validate_safe(item)

    def _validate_expression(self, expression: str) -> None:
        forbidden = (";", "--", "/*", "*/", "__", "import", "exec", "eval")
        if any(item in expression.lower() for item in forbidden):
            raise ValueError("Arbitrary code and unrestricted SQL are prohibited.")
        if not expression or not self.SAFE_EXPRESSION.fullmatch(expression):
            raise ValueError("Expression is outside the bounded interface.")

    def _audit(self, action: str, scope: BIScope, **metadata: Any) -> None:
        safe = {
            key: value
            for key, value in metadata.items()
            if not self.SECRET_KEYS.search(key)
        }
        self.audit.append(
            AuditEntry(
                action, scope.actor, scope.tenant, scope.workspace, utcnow(), safe
            )
        )

    def _create(
        self,
        records: dict[str, ScopedT],
        record: ScopedT,
        scope: BIScope,
        metric: str | None = None,
    ) -> ScopedT:
        self._require(scope, "business_intelligence:write")
        if not self._in_scope(record, scope):
            raise PermissionError("Cross-tenant or cross-workspace write denied.")
        if record.id in records:
            raise ValueError("Resource already exists.")
        self._validate_safe(asdict(record))
        records[record.id] = record
        if metric:
            self.metrics.increment(metric)
        self._audit(
            "resource.create",
            scope,
            resource_id=record.id,
            resource_type=type(record).__name__,
        )
        return record

    def create_workspace(self, record: BIWorkspace, scope: BIScope) -> BIWorkspace:
        return self._create(self.workspaces, record, scope, "bi_workspaces_total")

    def set_workspace_status(
        self, workspace_id: str, status: WorkspaceStatus, scope: BIScope
    ) -> BIWorkspace:
        self._require(scope, "business_intelligence:write")
        record = self._get(self.workspaces, workspace_id, scope)
        if status not in self.TRANSITIONS[record.status]:
            raise ValueError("Invalid BI workspace lifecycle transition.")
        record.status = status
        self._audit(
            "workspace.status",
            scope,
            workspace_id=workspace_id,
            status=status.value,
        )
        return record

    def add_data_source(self, record: DataSource, scope: BIScope) -> DataSource:
        if record.credential_reference and not self.CREDENTIAL_REFERENCE.fullmatch(
            record.credential_reference
        ):
            raise ValueError(
                "Use an opaque credential reference, never plaintext credentials."
            )
        return self._create(self.data_sources, record, scope, "bi_data_sources_total")

    def add_dataset(self, record: Dataset, scope: BIScope) -> Dataset:
        self._get(self.data_sources, record.data_source_id, scope)
        return self._create(self.datasets, record, scope, "bi_datasets_total")

    def add_metric(self, record: Metric, scope: BIScope) -> Metric:
        self._validate_expression(record.formula)
        return self._create(self.metrics_definitions, record, scope)

    def add_dimension(self, record: Dimension, scope: BIScope) -> Dimension:
        return self._create(self.dimensions, record, scope)

    def add_measure(self, record: Measure, scope: BIScope) -> Measure:
        self._validate_expression(record.expression)
        return self._create(self.measures, record, scope)

    def add_semantic_model(
        self, record: SemanticModel, scope: BIScope
    ) -> SemanticModel:
        for dataset_id in record.dataset_ids:
            self._get(self.datasets, dataset_id, scope)
        return self._create(self.semantic_models, record, scope)

    def execute_query(self, query: BIQuery, scope: BIScope) -> dict[str, Any]:
        self._require(scope, "business_intelligence:query")
        started = time.monotonic()
        try:
            self._get(self.datasets, query.dataset_id, scope)
            if query.row_limit < 1 or query.row_limit > self.max_rows:
                raise ValueError("Query row limit exceeds policy.")
            if query.timeout_seconds < 1 or query.timeout_seconds > self.max_timeout:
                raise ValueError("Query timeout exceeds policy.")
            for value in (*query.metrics, *query.dimensions, *query.sorting):
                self._validate_expression(value)
            self._validate_safe(query.filters)
            self.queries[query.id] = query
            self.metrics.increment("bi_queries_total")
            result = {
                "query_id": query.id,
                "columns": [],
                "rows": [],
                "row_count": 0,
            }
            self._audit(
                "query.execute",
                scope,
                query_id=query.id,
                row_limit=query.row_limit,
            )
            return result
        except Exception:
            self.metrics.increment("bi_query_failures_total")
            raise
        finally:
            self.metrics.increment(
                "bi_query_latency_seconds", time.monotonic() - started
            )

    def add_report(self, record: Report, scope: BIScope) -> Report:
        return self._create(self.reports, record, scope, "bi_reports_total")

    def add_dashboard(self, record: Dashboard, scope: BIScope) -> Dashboard:
        return self._create(self.dashboards, record, scope, "bi_dashboards_total")

    def add_visualization(self, record: Visualization, scope: BIScope) -> Visualization:
        if record.type is VisualizationType.CUSTOM:
            self._validate_safe(record.configuration)
        return self._create(self.visualizations, record, scope)

    def add_insight(self, record: Insight, scope: BIScope) -> Insight:
        return self._create(self.insights, record, scope, "bi_insights_total")

    def add_alert(self, record: Alert, scope: BIScope) -> Alert:
        return self._create(self.alerts, record, scope, "bi_alerts_total")

    def add_subscription(self, record: Subscription, scope: BIScope) -> Subscription:
        return self._create(self.subscriptions, record, scope)

    def request_export(self, record: ExportRequest, scope: BIScope) -> ExportRequest:
        self._require(scope, "business_intelligence:export")
        if record.row_limit > self.max_rows or record.size_limit_bytes > 50_000_000:
            raise ValueError("Export exceeds policy limits.")
        elevated = BIScope(
            scope.tenant,
            scope.workspace,
            scope.actor,
            scope.permissions | {"business_intelligence:write"},
        )
        return self._create(self.exports, record, elevated, "bi_exports_total")

    def add_governance_policy(
        self, record: GovernancePolicy, scope: BIScope
    ) -> GovernancePolicy:
        return self._create(self.governance, record, scope)

    def resource(self, name: str, scope: BIScope) -> list[dict[str, Any]]:
        self._require(scope, "business_intelligence:read")
        mapping = {
            "workspaces": self.workspaces,
            "data-sources": self.data_sources,
            "datasets": self.datasets,
            "semantic-models": self.semantic_models,
            "metrics": self.metrics_definitions,
            "queries": self.queries,
            "reports": self.reports,
            "dashboards": self.dashboards,
            "insights": self.insights,
            "alerts": self.alerts,
            "subscriptions": self.subscriptions,
            "exports": self.exports,
            "governance": self.governance,
        }
        records = mapping[name]
        return [
            asdict(item) for item in records.values() if self._in_scope(item, scope)
        ]

    def dashboard(self, scope: BIScope) -> dict[str, Any]:
        resources = (
            "workspaces",
            "data-sources",
            "datasets",
            "semantic-models",
            "metrics",
            "reports",
            "dashboards",
            "insights",
            "alerts",
            "subscriptions",
            "governance",
        )
        return {name: self.resource(name, scope) for name in resources} | {
            "metrics_snapshot": self.metrics.snapshot()
        }


EnterpriseAIBusinessIntelligencePlatform = BusinessIntelligencePlatform
