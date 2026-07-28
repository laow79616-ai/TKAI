"""Tenant-isolated reporting and analytics for existing TikTok modules."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from datetime import timedelta
from statistics import fmean
from time import perf_counter
from typing import Any

from .adapters import MODULES, AnalyticsModulePort, NullAnalyticsModulePort
from .metrics import AnalyticsMetrics
from .models import (
    KPI,
    AnalyticsScope,
    AnalyticsStatus,
    AnalyticsWorkspace,
    AuditRecord,
    DataPoint,
    ExportFormat,
    ExportRecord,
    Forecast,
    HistorySnapshot,
    Insight,
    Period,
    Report,
    Trend,
    utcnow,
)


class TikTokAIAnalyticsCenter:
    """Unified analytics plane; all module access is read-only and reference based."""

    def __init__(self, ports: dict[str, AnalyticsModulePort] | None = None) -> None:
        null = NullAnalyticsModulePort()
        self.ports = {name: (ports or {}).get(name, null) for name in MODULES}
        self.workspaces: dict[str, AnalyticsWorkspace] = {}
        self.reports: dict[str, Report] = {}
        self.kpis: dict[str, KPI] = {}
        self.trends: dict[str, Trend] = {}
        self.forecasts: dict[str, Forecast] = {}
        self.history: dict[str, HistorySnapshot] = {}
        self.insights: dict[str, Insight] = {}
        self.exports: dict[str, ExportRecord] = {}
        self.audit: list[AuditRecord] = []
        self.metrics = AnalyticsMetrics()

    @staticmethod
    def _require(scope: AnalyticsScope, permission: str) -> None:
        required = f"tiktok:analytics:{permission}"
        if (
            required not in scope.permissions
            and "tiktok:analytics:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {required}")

    @staticmethod
    def _scoped(item: Any, scope: AnalyticsScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _record(
        self, scope: AnalyticsScope, action: str, resource: str, detail: str
    ) -> None:
        forbidden = ("password=", "secret=", "token=", "cookie=", "session=")
        if any(marker in detail.casefold() for marker in forbidden):
            raise ValueError("Secrets are forbidden in analytics audit records.")
        self.audit.append(
            AuditRecord(
                scope.actor, action, resource, scope.tenant, scope.workspace, detail
            )
        )

    def scoped_values(self, values: Any, scope: AnalyticsScope) -> list[Any]:
        return [
            item
            for item in values
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def create_workspace(
        self, workspace: AnalyticsWorkspace, scope: AnalyticsScope
    ) -> AnalyticsWorkspace:
        self._require(scope, "write")
        self._scoped(workspace, scope)
        workspace.validate()
        if workspace.id in self.workspaces:
            raise ValueError("Analytics workspace ID must be unique.")
        self.workspaces[workspace.id] = workspace
        self._record(scope, "workspace.created", workspace.id, "create")
        return workspace

    def transition(
        self, reference: str, status: AnalyticsStatus, scope: AnalyticsScope
    ) -> AnalyticsWorkspace:
        self._require(scope, "write")
        item = self.workspaces[reference]
        self._scoped(item, scope)
        allowed = {
            AnalyticsStatus.DRAFT: {
                AnalyticsStatus.GENERATING,
                AnalyticsStatus.ARCHIVED,
            },
            AnalyticsStatus.GENERATING: {AnalyticsStatus.READY, AnalyticsStatus.DRAFT},
            AnalyticsStatus.READY: {
                AnalyticsStatus.GENERATING,
                AnalyticsStatus.ARCHIVED,
            },
            AnalyticsStatus.ARCHIVED: {AnalyticsStatus.DRAFT, AnalyticsStatus.DELETED},
            AnalyticsStatus.DELETED: set(),
        }
        if status not in allowed[item.status]:
            raise ValueError(
                f"Invalid analytics transition: {item.status.value} -> {status.value}"
            )
        item.status, item.version = status, item.version + 1
        self._record(scope, "workspace.transition", reference, status.value)
        return item

    def generate_report(self, report: Report, scope: AnalyticsScope) -> Report:
        started = perf_counter()
        self._require(scope, "generate")
        self._scoped(report, scope)
        try:
            report.status = AnalyticsStatus.READY
            report.generated_at = utcnow()
            self.reports[report.id] = report
            self.metrics.increment("tiktok_reports_total")
            self._record(scope, "report.generated", report.id, report.report_type.value)
            return report
        finally:
            self.metrics.set("tiktok_report_latency_seconds", perf_counter() - started)

    def record_kpi(self, kpi: KPI, scope: AnalyticsScope) -> KPI:
        self._require(scope, "write")
        self._scoped(kpi, scope)
        self.kpis[kpi.id] = kpi
        self.metrics.increment("tiktok_kpis_total")
        self._record(scope, "kpi.recorded", kpi.id, kpi.kind.value)
        return kpi

    def analyze_trend(
        self,
        reference: str,
        metric: str,
        period: Period,
        points: list[DataPoint],
        scope: AnalyticsScope,
    ) -> Trend:
        self._require(scope, "generate")
        if not points:
            raise ValueError("Trend analysis requires historical data points.")
        first, last = points[0].value, points[-1].value
        growth = ((last - first) / abs(first) * 100) if first else 0
        trend = Trend(
            reference,
            scope.tenant,
            scope.workspace,
            metric,
            period,
            points,
            comparison=last - first,
            growth=growth,
            regression=last < first,
        )
        self.trends[reference] = trend
        self.metrics.increment("tiktok_trends_total")
        self._record(scope, "trend.analyzed", reference, metric)
        return trend

    def create_forecast(
        self,
        reference: str,
        metric: str,
        points: list[DataPoint],
        forecast_window: int,
        scope: AnalyticsScope,
    ) -> Forecast:
        self._require(scope, "generate")
        if len(points) < 2 or not 1 <= forecast_window <= 365:
            raise ValueError("Forecast requires history and a window within [1, 365].")
        deltas = [
            current.value - previous.value
            for previous, current in zip(points, points[1:], strict=False)
        ]
        step = fmean(deltas)
        projection = [
            DataPoint(
                points[-1].timestamp + timedelta(days=index),
                points[-1].value + step * index,
            )
            for index in range(1, forecast_window + 1)
        ]
        spread = max(abs(value) for value in deltas)
        confidence = max(
            0.0, min(1.0, 1 - spread / (abs(fmean([p.value for p in points])) + 1))
        )
        forecast = Forecast(
            reference,
            scope.tenant,
            scope.workspace,
            metric,
            forecast_window,
            projection,
            step,
            min(0.0, step),
            step,
            confidence,
        )
        self.forecasts[reference] = forecast
        self.metrics.increment("tiktok_forecasts_total")
        self._record(scope, "forecast.created", reference, metric)
        return forecast

    def snapshot(
        self, snapshot: HistorySnapshot, scope: AnalyticsScope
    ) -> HistorySnapshot:
        self._require(scope, "write")
        self._scoped(snapshot, scope)
        if not 1 <= snapshot.retention_days <= 3650:
            raise ValueError("Retention must be within [1, 3650] days.")
        self.history[snapshot.id] = snapshot
        self._record(scope, "history.snapshotted", snapshot.id, "create")
        return snapshot

    def archive_snapshot(
        self, reference: str, archived: bool, scope: AnalyticsScope
    ) -> HistorySnapshot:
        self._require(scope, "archive")
        item = self.history[reference]
        self._scoped(item, scope)
        item.archived = archived
        self._record(
            scope, "history.archived" if archived else "history.restored", reference, ""
        )
        return item

    def create_insight(self, insight: Insight, scope: AnalyticsScope) -> Insight:
        self._require(scope, "generate")
        self._scoped(insight, scope)
        self.insights[insight.id] = insight
        self.metrics.increment("tiktok_insights_total")
        self._record(scope, "insight.created", insight.id, insight.trend_summary)
        return insight

    def export_report(
        self,
        reference: str,
        format: ExportFormat,
        export_id: str,
        scope: AnalyticsScope,
    ) -> tuple[ExportRecord, str]:
        self._require(scope, "export")
        report = self.reports[reference]
        self._scoped(report, scope)
        payload = {
            "id": report.id,
            "name": report.name,
            "report_type": report.report_type.value,
            "dataset_reference": report.dataset_reference,
        }
        if format is ExportFormat.JSON:
            content = json.dumps(payload, sort_keys=True)
        elif format is ExportFormat.CSV:
            stream = io.StringIO()
            writer = csv.DictWriter(stream, fieldnames=list(payload))
            writer.writeheader()
            writer.writerow(payload)
            content = stream.getvalue()
        else:
            content = f"{format.value}://{export_id}"
        record = ExportRecord(
            export_id,
            scope.tenant,
            scope.workspace,
            reference,
            format,
            f"analytics-export://{export_id}",
            scope.actor,
        )
        self.exports[export_id] = record
        self._record(scope, "report.exported", reference, format.value)
        return record, content

    def overview(self, scope: AnalyticsScope) -> dict[str, Any]:
        self._require(scope, "read")
        module_metrics = {
            name: port.metrics(scope) for name, port in self.ports.items()
        }
        return {
            "modules": module_metrics,
            "reports": len(self.scoped_values(self.reports.values(), scope)),
            "kpis": [
                asdict(item) for item in self.scoped_values(self.kpis.values(), scope)
            ],
            "trends": len(self.scoped_values(self.trends.values(), scope)),
            "forecasts": len(self.scoped_values(self.forecasts.values(), scope)),
            "insights": len(self.scoped_values(self.insights.values(), scope)),
        }

    def dashboard(self, scope: AnalyticsScope) -> dict[str, Any]:
        return {
            "title": "TikTok AI Analytics Center",
            "sections": [
                "Overview",
                "KPIs",
                "Reports",
                "Trends",
                "Forecast",
                "Insights",
                "History",
                "Exports",
            ],
            "overview": self.overview(scope),
        }
