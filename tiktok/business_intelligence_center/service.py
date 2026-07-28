"""Unified, read-only and advisory TikTok business analytics service."""

from __future__ import annotations

import csv
import io
import json
from datetime import timedelta
from time import perf_counter
from typing import Any

from .adapters import BoundedTestDouble, ReadOnlyAnalyticsPort
from .metrics import BusinessIntelligenceMetrics
from .models import (
    AuditEvent,
    BIScope,
    BIWorkspace,
    Dataset,
    Insight,
    IntegrityStatus,
    Metric,
    Query,
    SemanticModel,
    WorkspaceStatus,
    utcnow,
    validate_metadata,
    validate_reference,
)

MAX_ROWS = 10_000
MAX_PAGE_SIZE = 500
MAX_TIMEOUT_SECONDS = 30
MAX_TIME_RANGE = timedelta(days=366)
MAX_EXPORT_BYTES = 10_000_000
ALLOWED_AGGREGATIONS = frozenset(
    {
        "count",
        "distinct_count",
        "sum",
        "average",
        "minimum",
        "maximum",
        "ratio",
        "percentage",
        "duration",
    }
)
ALLOWED_DIMENSIONS = frozenset(
    {
        "workspace",
        "project",
        "campaign",
        "lead_stage",
        "crm_stage",
        "journey_stage",
        "content_type",
        "publishing_status",
        "workflow",
        "task_type",
        "resource_type",
        "risk_level",
        "region",
        "language",
        "time",
    }
)
KPI_NAMES = (
    "lead_qualification_rate",
    "lead_assignment_time",
    "consent_coverage",
    "crm_conversion_reference",
    "opportunity_progress",
    "journey_completion_rate",
    "journey_drop_off_rate",
    "campaign_completion_rate",
    "content_pipeline_throughput",
    "publishing_success_rate",
    "workflow_success_rate",
    "execution_success_rate",
    "recovery_success_rate",
    "runtime_availability",
    "resource_utilization",
    "risk_score",
    "growth_trend",
)
SENSITIVE_FIELDS = frozenset({"email", "phone", "full_name", "ip_address"})
PROTECTED_QUERY_FIELDS = frozenset(
    {
        "race",
        "ethnicity",
        "religion",
        "health",
        "disability",
        "sexual_orientation",
        "gender_identity",
        "political_opinion",
        "biometric",
        "genetic",
    }
)
TRANSITIONS = {
    WorkspaceStatus.DRAFT: {WorkspaceStatus.COLLECTING, WorkspaceStatus.ARCHIVED},
    WorkspaceStatus.COLLECTING: {WorkspaceStatus.MODELING, WorkspaceStatus.ARCHIVED},
    WorkspaceStatus.MODELING: {WorkspaceStatus.READY, WorkspaceStatus.ARCHIVED},
    WorkspaceStatus.READY: {WorkspaceStatus.REVIEW, WorkspaceStatus.ARCHIVED},
    WorkspaceStatus.REVIEW: {WorkspaceStatus.APPROVED, WorkspaceStatus.READY},
    WorkspaceStatus.APPROVED: {WorkspaceStatus.ARCHIVED},
    WorkspaceStatus.ARCHIVED: {WorkspaceStatus.DELETED},
    WorkspaceStatus.DELETED: set(),
}


class TikTokBusinessIntelligenceCenter:
    def __init__(self, adapter: ReadOnlyAnalyticsPort | None = None) -> None:
        self.adapter = adapter or BoundedTestDouble()
        self.workspaces: dict[str, BIWorkspace] = {}
        self.datasets: dict[str, Dataset] = {}
        self.semantic_models: dict[str, SemanticModel] = {}
        self.kpis: dict[str, dict[str, Any]] = {}
        self.metric_definitions: dict[str, Metric] = {}
        self.dashboards: dict[str, dict[str, Any]] = {}
        self.reports: dict[str, dict[str, Any]] = {}
        self.comparisons: dict[str, dict[str, Any]] = {}
        self.trends: dict[str, dict[str, Any]] = {}
        self.forecasts: dict[str, dict[str, Any]] = {}
        self.insights: dict[str, Insight] = {}
        self.snapshots: dict[str, dict[str, Any]] = {}
        self.exports: dict[str, dict[str, Any]] = {}
        self.governance_records: dict[str, dict[str, Any]] = {}
        self.audit: list[AuditEvent] = []
        self.history_records: list[dict[str, Any]] = []
        self.metrics = BusinessIntelligenceMetrics()

    @staticmethod
    def _require(scope: BIScope, action: str) -> None:
        permission = f"tiktok:business-intelligence:{action}"
        if (
            permission not in scope.permissions
            and "tiktok:business-intelligence:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _scoped(item: Any, scope: BIScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def scoped_values(self, values: Any, scope: BIScope) -> list[Any]:
        self._require(scope, "read")
        return [
            i
            for i in values
            if (i.get("tenant") if isinstance(i, dict) else i.tenant) == scope.tenant
            and (i.get("workspace") if isinstance(i, dict) else i.workspace)
            == scope.workspace
        ]

    def _record(self, scope: BIScope, action: str, reference: str) -> None:
        if any(
            word in reference.casefold() for word in ("token=", "cookie=", "secret=")
        ):
            raise ValueError("Secrets are forbidden in audit events.")
        self.audit.append(
            AuditEvent(scope.tenant, scope.workspace, scope.actor, action, reference)
        )
        self.history_records.append(
            {
                "tenant": scope.tenant,
                "workspace": scope.workspace,
                "actor": scope.actor,
                "action": action,
                "reference": reference,
                "timestamp": utcnow(),
            }
        )

    def create_workspace(self, item: BIWorkspace, scope: BIScope) -> BIWorkspace:
        self._require(scope, "admin")
        self._scoped(item, scope)
        item.validate()
        if item.id in self.workspaces:
            raise ValueError("BI workspace ID must be unique.")
        self.workspaces[item.id] = item
        self.metrics.increment("tiktok_business_intelligence_workspaces_total")
        self._record(scope, "workspace.created", f"ref://bi-workspace/{item.id}")
        return item

    def transition(
        self, identifier: str, status: WorkspaceStatus, scope: BIScope
    ) -> BIWorkspace:
        self._require(scope, "admin")
        item = self.workspaces[identifier]
        self._scoped(item, scope)
        if status not in TRANSITIONS[item.status]:
            raise ValueError(
                "Invalid BI lifecycle transition: "
                f"{item.status.value} -> {status.value}"
            )
        item.status = status
        item.version += 1
        item.updated_at = utcnow()
        self._record(
            scope,
            f"workspace.transition.{status.value}",
            f"ref://bi-workspace/{identifier}",
        )
        return item

    def register_dataset(self, item: Dataset, scope: BIScope) -> Dataset:
        self._require(scope, "admin")
        self._scoped(item, scope)
        item.validate()
        if not item.consent_aware or not item.purpose.strip():
            raise PermissionError(
                "Consent awareness and purpose limitation are required."
            )
        if item.integrity_status is not IntegrityStatus.VALID:
            raise ValueError("Only integrity-validated datasets may be registered.")
        self.datasets[item.id] = item
        self.metrics.increment("tiktok_business_intelligence_datasets_total")
        self.metrics.set(
            "tiktok_business_intelligence_data_freshness_seconds",
            item.freshness_seconds,
        )
        self._record(scope, "dataset.registered", item.source_reference)
        return item

    def register_semantic_model(
        self, item: SemanticModel, scope: BIScope
    ) -> SemanticModel:
        self._require(scope, "admin")
        self._scoped(item, scope)
        validate_metadata(item.business_definitions)
        self.semantic_models[item.id] = item
        self._record(
            scope, "semantic-model.registered", f"ref://semantic-model/{item.id}"
        )
        return item

    def register_metric(self, item: Metric, scope: BIScope) -> Metric:
        self._require(scope, "admin")
        self._scoped(item, scope)
        if item.aggregation not in ALLOWED_AGGREGATIONS:
            raise ValueError("Metric aggregation is not supported.")
        validate_reference(item.target_reference)
        validate_reference(item.threshold_reference)
        self.metric_definitions[item.id] = item
        self._record(scope, "metric.registered", f"ref://metric/{item.id}")
        return item

    def execute_query(self, item: Query, scope: BIScope) -> dict[str, Any]:
        started = perf_counter()
        self._require(scope, "query")
        self._scoped(item, scope)
        if item.dataset not in self.datasets:
            raise KeyError("Dataset is not registered.")
        dataset = self.datasets[item.dataset]
        self._scoped(dataset, scope)
        if dataset.integrity_status is not IntegrityStatus.VALID:
            raise ValueError("Dataset integrity validation failed.")
        if (
            not 1 <= item.page_size <= MAX_PAGE_SIZE
            or not 1 <= item.row_limit <= MAX_ROWS
        ):
            raise ValueError("Pagination or row limit exceeds bounded query limits.")
        if not 1 <= item.timeout_seconds <= MAX_TIMEOUT_SECONDS:
            raise ValueError("Query timeout exceeds the bounded limit.")
        if (
            item.time_start > item.time_end
            or item.time_end - item.time_start > MAX_TIME_RANGE
        ):
            raise ValueError("Query time range exceeds the bounded limit.")
        if set(item.dimensions) - ALLOWED_DIMENSIONS:
            raise ValueError("Unsupported query dimension.")
        if set(item.kpis) - set(KPI_NAMES) - set(self.kpis):
            raise ValueError("Unsupported KPI.")
        validate_metadata(item.filters)
        offset = (item.page - 1) * item.page_size
        rows = [
            self._mask_sensitive(row)
            for row in self.adapter.read(item.dataset, item.filters, item.row_limit)
        ]
        rows = rows[offset : offset + min(item.row_limit, item.page_size)]
        self.metrics.increment("tiktok_business_intelligence_queries_total")
        self.metrics.set(
            "tiktok_business_intelligence_query_seconds", perf_counter() - started
        )
        self._record(scope, "query.executed", f"ref://query/{item.id}")
        return {
            "id": item.id,
            "rows": rows,
            "row_count": len(rows),
            "page": item.page,
            "page_size": item.page_size,
            "bounded": True,
            "read_only": True,
        }

    @staticmethod
    def _mask_sensitive(row: dict[str, Any]) -> dict[str, Any]:
        result = {}
        for key, value in row.items():
            normalized = key.casefold().replace("-", "_")
            if normalized in PROTECTED_QUERY_FIELDS:
                raise ValueError(
                    "Protected attributes are prohibited in analytical results."
                )
            result[key] = "***" if normalized in SENSITIVE_FIELDS else value
        return result

    def create_artifact(
        self, kind: str, identifier: str, payload: dict[str, Any], scope: BIScope
    ) -> dict[str, Any]:
        self._require(scope, "admin")
        validate_metadata(payload)
        stores = {
            "dashboard": self.dashboards,
            "report": self.reports,
            "comparison": self.comparisons,
            "trend": self.trends,
            "forecast": self.forecasts,
            "snapshot": self.snapshots,
            "governance": self.governance_records,
        }
        if kind not in stores:
            raise ValueError("Unsupported BI artifact.")
        record = {
            "id": identifier,
            "tenant": scope.tenant,
            "workspace": scope.workspace,
            "advisory": True,
            "version": 1,
            **payload,
        }
        if kind == "forecast" and (
            not 0 <= float(record.get("confidence", -1)) <= 1
            or not record.get("evidence_references")
        ):
            raise ValueError("Forecast confidence and evidence are required.")
        stores[kind][identifier] = record
        metric = {
            "dashboard": "tiktok_business_intelligence_dashboards_total",
            "report": "tiktok_business_intelligence_reports_total",
            "forecast": "tiktok_business_intelligence_forecasts_total",
        }.get(kind)
        if metric:
            self.metrics.increment(metric)
        self._record(scope, f"{kind}.created", f"ref://{kind}/{identifier}")
        return record

    def add_insight(self, item: Insight, scope: BIScope) -> Insight:
        self._require(scope, "admin")
        self._scoped(item, scope)
        if not 0 <= item.confidence <= 1 or not item.evidence_references:
            raise ValueError("Insight confidence and evidence are required.")
        for ref in item.evidence_references:
            validate_reference(ref)
        self.insights[item.id] = item
        self.metrics.increment("tiktok_business_intelligence_insights_total")
        self._record(scope, "insight.created", f"ref://insight/{item.id}")
        return item

    def export(
        self,
        identifier: str,
        result: dict[str, Any],
        format: str,
        scope: BIScope,
        *,
        row_limit: int = 1000,
        size_limit: int = MAX_EXPORT_BYTES,
    ) -> dict[str, Any]:
        self._require(scope, "export")
        if format not in {"csv", "json"}:
            raise ValueError(
                "Only bounded CSV and JSON exports are generated; "
                "XLSX/PDF use references."
            )
        if not 1 <= row_limit <= MAX_ROWS or not 1 <= size_limit <= MAX_EXPORT_BYTES:
            raise ValueError("Export bounds exceeded.")
        rows = list(result.get("rows", []))[:row_limit]
        if format == "json":
            content = json.dumps(rows, default=str)
        else:
            stream = io.StringIO()
            fields = list(rows[0]) if rows else []
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
            content = stream.getvalue()
        if len(content.encode()) > size_limit:
            raise ValueError("Export exceeds the authorized size limit.")
        record = {
            "id": identifier,
            "tenant": scope.tenant,
            "workspace": scope.workspace,
            "format": format,
            "row_count": len(rows),
            "size_bytes": len(content.encode()),
            "content": content,
            "authorized": True,
            "audit": True,
        }
        self.exports[identifier] = record
        self.metrics.increment("tiktok_business_intelligence_exports_total")
        self._record(scope, "export.created", f"ref://export/{identifier}")
        return record

    def dashboard(self, scope: BIScope) -> dict[str, Any]:
        self._require(scope, "read")
        return {
            "title": "TikTok Business Intelligence Center",
            "sections": [
                "BI Overview",
                "Workspaces",
                "Datasets",
                "Semantic Models",
                "KPIs",
                "Metrics",
                "Dashboards",
                "Reports",
                "Comparisons",
                "Trends",
                "Forecasts",
                "Insights",
                "Snapshots",
                "Exports",
                "Governance",
                "Analytics",
            ],
            "counts": {
                "workspaces": len(self.scoped_values(self.workspaces.values(), scope)),
                "datasets": len(self.scoped_values(self.datasets.values(), scope)),
                "reports": len(self.scoped_values(self.reports.values(), scope)),
                "insights": len(self.scoped_values(self.insights.values(), scope)),
            },
            "safety": {
                "advisory_only": True,
                "direct_execution": False,
                "direct_publishing": False,
                "direct_outreach": False,
                "approval_gated_handoffs": True,
                "restriction_aware": True,
            },
        }

    def analytics(self, scope: BIScope) -> dict[str, Any]:
        started = perf_counter()
        self._require(scope, "read")
        result = {
            "kpis": list(KPI_NAMES),
            "dimensions": sorted(ALLOWED_DIMENSIONS),
            "measures": sorted(ALLOWED_AGGREGATIONS),
            "bounded": True,
            "arbitrary_sql": False,
            "arbitrary_code": False,
        }
        self.metrics.set(
            "tiktok_business_intelligence_analysis_seconds", perf_counter() - started
        )
        self._record(scope, "analytics.viewed", "ref://analytics/overview")
        return result

    def history(self, scope: BIScope) -> list[dict[str, Any]]:
        self._require(scope, "read")
        return self.scoped_values(self.history_records, scope)
