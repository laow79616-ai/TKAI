"""Explainable, bounded, advisory-only performance analytics."""

from __future__ import annotations

from dataclasses import asdict
from time import perf_counter
from typing import Any

from .adapters import INTEGRATION_MODULES, BoundedTestDouble, ReadOnlyPerformancePort
from .metrics import PerformanceMetrics
from .models import (
    MAX_RESULTS,
    Anomaly,
    AuditEvent,
    Benchmark,
    Comparison,
    Dataset,
    Forecast,
    Insight,
    Metric,
    MetricKind,
    PerformanceProfile,
    PerformanceStatus,
    Recommendation,
    Report,
    ReportKind,
    RequestScope,
    Snapshot,
    TimeRange,
    Trend,
    utcnow,
    validate_metadata,
    validate_reference,
)

TRANSITIONS: dict[PerformanceStatus, frozenset[PerformanceStatus]] = {
    PerformanceStatus.DRAFT: frozenset(
        {PerformanceStatus.COLLECTING, PerformanceStatus.ARCHIVED}
    ),
    PerformanceStatus.COLLECTING: frozenset({PerformanceStatus.ANALYZING}),
    PerformanceStatus.ANALYZING: frozenset({PerformanceStatus.READY}),
    PerformanceStatus.READY: frozenset(
        {PerformanceStatus.REVIEW, PerformanceStatus.ANALYZING}
    ),
    PerformanceStatus.REVIEW: frozenset(
        {PerformanceStatus.APPROVED, PerformanceStatus.READY}
    ),
    PerformanceStatus.APPROVED: frozenset({PerformanceStatus.ARCHIVED}),
    PerformanceStatus.ARCHIVED: frozenset({PerformanceStatus.DELETED}),
    PerformanceStatus.DELETED: frozenset(),
}

DIMENSIONS = frozenset(
    {
        "account", "workspace", "project", "campaign", "content_type", "workflow",
        "task_type", "resource_type", "browser_node", "device_type", "proxy_region",
        "status", "risk_level", "time",
    }
)

UNSAFE_TERMS = (
    "captcha bypass", "restriction circumvention", "security bypass",
    "anti-detection guarantee", "spam automation", "engagement manipulation",
    "unsolicited bulk", "mass action",
)


class TikTokPerformanceInsightsCenter:
    """In-memory analytical layer; it exposes no execution or publishing method."""

    def __init__(self, inputs: ReadOnlyPerformancePort | None = None) -> None:
        self.input_port = inputs or BoundedTestDouble()
        self.profiles: dict[str, PerformanceProfile] = {}
        self.datasets: dict[str, Dataset] = {}
        self.metrics_evaluated: dict[str, Metric] = {}
        self.benchmarks: dict[str, Benchmark] = {}
        self.comparisons: dict[str, Comparison] = {}
        self.trends: dict[str, Trend] = {}
        self.anomalies: dict[str, Anomaly] = {}
        self.forecasts: dict[str, Forecast] = {}
        self.insights: dict[str, Insight] = {}
        self.recommendations: dict[str, Recommendation] = {}
        self.reports: dict[str, Report] = {}
        self.snapshots: dict[str, Snapshot] = {}
        self.profile_history: list[dict[str, Any]] = []
        self.entity_history: list[dict[str, Any]] = []
        self.audit: list[AuditEvent] = []
        self.metrics = PerformanceMetrics()

    @staticmethod
    def _require(scope: RequestScope, action: str) -> None:
        permission = f"tiktok:performance:{action}"
        if permission not in scope.permissions and (
            "tiktok:performance:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _scoped(item: Any, scope: RequestScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def scoped_values(
        self, values: Any, scope: RequestScope, limit: int = MAX_RESULTS
    ) -> list[Any]:
        self._require(scope, "read")
        if not 1 <= limit <= MAX_RESULTS:
            raise ValueError("Result limit must be within [1, 500].")
        return [
            item for item in values
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ][:limit]

    def _record(self, item: Any, scope: RequestScope, action: str) -> None:
        reference = f"ref://performance/{type(item).__name__.lower()}/{item.id}"
        self.audit.append(
            AuditEvent(item.tenant, item.workspace, scope.actor, action, reference)
        )
        payload = asdict(item)
        validate_metadata(payload.get("metadata", {}))
        self.entity_history.append(
            {"entity_type": type(item).__name__, "action": action, **payload}
        )

    def create_profile(
        self, profile: PerformanceProfile, scope: RequestScope
    ) -> PerformanceProfile:
        self._require(scope, "write")
        self._scoped(profile, scope)
        profile.validate()
        if profile.id in self.profiles:
            raise ValueError("Performance profile ID must be unique.")
        self.profiles[profile.id] = profile
        self.profile_history.append(profile.to_dict())
        self._record(profile, scope, "profile.created")
        self.metrics.increment("tiktok_performance_profiles_total")
        return profile

    def transition(
        self, profile_id: str, status: PerformanceStatus, scope: RequestScope
    ) -> PerformanceProfile:
        self._require(scope, "write")
        profile = self.profiles[profile_id]
        self._scoped(profile, scope)
        if status not in TRANSITIONS[profile.status]:
            raise ValueError(
                f"Invalid performance transition: {profile.status.value} "
                f"-> {status.value}"
            )
        profile.status = status
        profile.version += 1
        profile.updated_at = utcnow()
        self.profile_history.append(profile.to_dict())
        self._record(profile, scope, f"profile.transition.{status.value}")
        return profile

    def add_dataset(self, dataset: Dataset, scope: RequestScope) -> Dataset:
        self._require(scope, "analyze")
        self._scoped(dataset, scope)
        dataset.time_range.validate()
        if dataset.source_module not in INTEGRATION_MODULES:
            raise ValueError("Dataset source must be an approved integration module.")
        validate_reference(dataset.source_reference)
        validate_reference(dataset.schema_reference)
        validate_reference(dataset.encrypted_reference, encrypted=True)
        if dataset.integrity_status not in {"valid", "verified"}:
            raise ValueError("Dataset integrity validation failed.")
        if dataset.freshness_seconds < 0:
            raise ValueError("Dataset freshness cannot be negative.")
        self.datasets[dataset.id] = dataset
        self._record(dataset, scope, "dataset.added")
        self.metrics.increment("tiktok_performance_datasets_total")
        self.metrics.set(
            "tiktok_performance_data_freshness_seconds", dataset.freshness_seconds
        )
        return dataset

    def evaluate_metric(self, metric: Metric, scope: RequestScope) -> Metric:
        started = perf_counter()
        self._require(scope, "analyze")
        self._scoped(metric, scope)
        if not set(metric.dimensions) <= DIMENSIONS:
            raise ValueError("Metric contains an unsupported dimension.")
        if metric.kind is MetricKind.CUSTOM_BOUNDED and not metric.custom_definition:
            raise ValueError("Custom metrics require a bounded definition.")
        self._evidence(metric.evidence_references)
        self.metrics_evaluated[metric.id] = metric
        self._record(metric, scope, "metric.evaluated")
        self.metrics.increment("tiktok_performance_metrics_total")
        self.metrics.set(
            "tiktok_performance_analysis_seconds", perf_counter() - started
        )
        return metric

    def add_benchmark(self, item: Benchmark, scope: RequestScope) -> Benchmark:
        self._add(item, self.benchmarks, scope, "benchmark.generated")
        validate_reference(item.reference)
        return item

    def compare(self, item: Comparison, scope: RequestScope) -> Comparison:
        self._evidence(item.evidence_references)
        self._add(item, self.comparisons, scope, "comparison.generated")
        self.metrics.increment("tiktok_performance_comparisons_total")
        return item

    def analyze_trend(self, item: Trend, scope: RequestScope) -> Trend:
        self._confidence(item.confidence)
        self._evidence(item.evidence_references)
        validate_reference(item.change_point_reference)
        self._add(item, self.trends, scope, "trend.generated")
        self.metrics.increment("tiktok_performance_trends_total")
        self.metrics.set("tiktok_performance_confidence", item.confidence)
        return item

    def add_anomaly(self, item: Anomaly, scope: RequestScope) -> Anomaly:
        validate_reference(item.explainable_evidence_reference)
        self._safe(item.summary)
        self._add(item, self.anomalies, scope, "anomaly.referenced")
        self.metrics.increment("tiktok_performance_anomalies_total")
        return item

    def forecast(self, item: Forecast, scope: RequestScope) -> Forecast:
        item.forecast_window.validate()
        self._confidence(item.confidence)
        self._evidence(item.evidence_references)
        if not item.advisory:
            raise ValueError("Forecasts must remain bounded and advisory.")
        self._add(item, self.forecasts, scope, "forecast.generated")
        self.metrics.increment("tiktok_performance_forecasts_total")
        self.metrics.set("tiktok_performance_confidence", item.confidence)
        return item

    def add_insight(self, item: Insight, scope: RequestScope) -> Insight:
        self._confidence(item.confidence)
        self._evidence(item.evidence_references)
        self._safe(f"{item.summary} {item.finding} {item.recommended_review}")
        for reference in (
            item.comparison_reference, item.trend_reference,
            item.anomaly_reference, item.forecast_reference,
        ):
            if reference:
                validate_reference(reference)
        self._add(item, self.insights, scope, "insight.generated")
        self.metrics.increment("tiktok_performance_insights_total")
        return item

    def recommend(
        self, item: Recommendation, scope: RequestScope
    ) -> Recommendation:
        self._safe(f"{item.title} {item.rationale}")
        self._evidence(item.evidence_references)
        if item.approved or (
            item.optimization_handoff_reference or item.decision_handoff_reference
        ):
            raise ValueError(
                "Recommendations must start advisory without direct handoffs."
            )
        self._add(item, self.recommendations, scope, "recommendation.generated")
        self.metrics.increment("tiktok_performance_recommendations_total")
        return item

    def add_report(self, item: Report, scope: RequestScope) -> Report:
        validate_reference(item.content_reference)
        if item.kind is ReportKind.CUSTOM_BOUNDED and not item.custom_definition:
            raise ValueError("Custom reports require a bounded definition.")
        self._add(item, self.reports, scope, "report.generated")
        self.metrics.increment("tiktok_performance_reports_total")
        return item

    def add_snapshot(self, item: Snapshot, scope: RequestScope) -> Snapshot:
        if not item.integrity_valid:
            raise ValueError("Snapshot integrity validation failed.")
        self._add(item, self.snapshots, scope, "snapshot.created")
        return item

    def integration_snapshot(
        self, scope: RequestScope, time_range: TimeRange, limit: int = 100
    ) -> dict[str, dict[str, Any]]:
        self._require(scope, "analyze")
        time_range.validate()
        return {
            module: self.input_port.snapshot(module, scope, time_range, limit)
            for module in INTEGRATION_MODULES
        }

    def _add(
        self, item: Any, store: dict[str, Any], scope: RequestScope, action: str
    ) -> None:
        self._require(scope, "analyze")
        self._scoped(item, scope)
        store[item.id] = item
        self._record(item, scope, action)

    @staticmethod
    def _confidence(value: float) -> None:
        if not 0 <= value <= 1:
            raise ValueError("Confidence must be within [0, 1].")

    @staticmethod
    def _evidence(references: list[str]) -> None:
        if not references:
            raise ValueError("Explainable evidence references are required.")
        for reference in references:
            validate_reference(reference)

    @staticmethod
    def _safe(text: str) -> None:
        if any(term in text.casefold() for term in UNSAFE_TERMS):
            raise ValueError("Unsafe performance guidance is forbidden.")

    def analytics(self, scope: RequestScope) -> dict[str, Any]:
        names: dict[str, Any] = {
            "profiles_total": self.profiles,
            "datasets_total": self.datasets,
            "metrics_evaluated": self.metrics_evaluated,
            "comparisons_generated": self.comparisons,
            "trends_generated": self.trends,
            "anomalies_generated": self.anomalies,
            "forecasts_generated": self.forecasts,
            "insights_generated": self.insights,
            "recommendations_generated": self.recommendations,
            "reports_generated": self.reports,
        }
        confidences = [
            item.confidence for store in (self.trends, self.forecasts, self.insights)
            for item in self.scoped_values(store.values(), scope)
        ]
        freshness = [
            item.freshness_seconds
            for item in self.scoped_values(self.datasets.values(), scope)
        ]
        result: dict[str, Any] = {
            name: len(self.scoped_values(store.values(), scope))
            for name, store in names.items()
        }
        result.update(
            {
                "average_analysis_time": self.metrics.values[
                    "tiktok_performance_analysis_seconds"
                ],
                "data_freshness": sum(freshness) / len(freshness)
                if freshness else 0.0,
                "confidence_distribution": {
                    "low": sum(value < 0.5 for value in confidences),
                    "medium": sum(0.5 <= value < 0.8 for value in confidences),
                    "high": sum(value >= 0.8 for value in confidences),
                },
            }
        )
        return result

    def history(self, scope: RequestScope) -> dict[str, Any]:
        self._require(scope, "read")
        return {
            "profile_history": [
                item for item in self.profile_history
                if item["tenant"] == scope.tenant
                and item["workspace"] == scope.workspace
            ],
            "entity_history": [
                item for item in self.entity_history
                if item["tenant"] == scope.tenant
                and item["workspace"] == scope.workspace
            ][:MAX_RESULTS],
            "audit_trail": [
                asdict(item) for item in self.scoped_values(self.audit, scope)
            ],
        }

    def dashboard(self, scope: RequestScope) -> dict[str, Any]:
        return {
            "sections": [
                "Performance Overview", "Profiles", "Datasets", "Metrics",
                "Benchmarks", "Comparisons", "Trends", "Anomalies", "Forecasts",
                "Insights", "Recommendations", "Reports", "Snapshots", "History",
                "Analytics",
            ],
            "performance_overview": self.analytics(scope),
            "advisory_only": True,
            "direct_execution": False,
        }
