"""Read-only forecasting and trend analysis for approved TikTok history."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from statistics import mean
from time import perf_counter
from typing import Any, Protocol, TypeVar

from .adapters import (
    PREDICTIVE_SOURCES,
    ReadOnlyPredictiveSource,
    ReferenceOnlyPredictiveSource,
)
from .metrics import PredictiveMetrics
from .models import (
    CapacityForecast,
    ConfidenceEstimate,
    Forecast,
    ForecastEvaluation,
    PredictiveContext,
    PredictiveProfile,
    PredictiveRecommendation,
    RiskForecast,
    Scenario,
    TrendAnalysis,
    utcnow,
    validate_ratio,
    validate_references,
)


class IdentifiedRecord(Protocol):
    @property
    def id(self) -> str: ...


T = TypeVar("T", bound=IdentifiedRecord)
TREND_DIRECTIONS = frozenset({"increasing", "decreasing", "stable", "volatile"})


class TikTokPredictiveAnalyticsCenter:
    """Generates explainable advisory projections without operational authority."""

    def __init__(
        self,
        sources: Mapping[str, ReadOnlyPredictiveSource] | None = None,
        *,
        max_history_days: int = 730,
        max_horizon_days: int = 365,
        max_results: int = 500,
    ) -> None:
        if not 1 <= max_history_days <= 3_650:
            raise ValueError("Historical range bound is unsupported.")
        if not 1 <= max_horizon_days <= 730:
            raise ValueError("Forecast horizon bound is unsupported.")
        if not 1 <= max_results <= 1_000:
            raise ValueError("Result bound is unsupported.")
        supplied = sources or {}
        self.sources = {
            name: supplied.get(name, ReferenceOnlyPredictiveSource(name))
            for name in PREDICTIVE_SOURCES
        }
        self.max_history_days = max_history_days
        self.max_horizon_days = max_horizon_days
        self.max_results = max_results
        self.profiles: dict[str, PredictiveProfile] = {}
        self.forecasts: dict[str, Forecast] = {}
        self.trends: dict[str, TrendAnalysis] = {}
        self.scenarios: dict[str, Scenario] = {}
        self.capacity: dict[str, CapacityForecast] = {}
        self.risk: dict[str, RiskForecast] = {}
        self.confidence: dict[str, ConfidenceEstimate] = {}
        self.recommendations: dict[str, PredictiveRecommendation] = {}
        self.history: list[dict[str, Any]] = []
        self.evaluations: dict[str, ForecastEvaluation] = {}
        self.audit: list[dict[str, Any]] = []
        self.metrics = PredictiveMetrics()

    @staticmethod
    def _require(context: PredictiveContext) -> None:
        if (
            "tiktok:predictive:read" not in context.permissions
            and "tiktok:predictive:admin" not in context.permissions
        ):
            raise PermissionError("RBAC permission required: tiktok:predictive:read")

    @staticmethod
    def _scoped(item: object, context: PredictiveContext) -> None:
        if (
            getattr(item, "tenant", None) != context.tenant
            or getattr(item, "workspace", None) != context.workspace
        ):
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _record(self, context: PredictiveContext, action: str, resource: str) -> None:
        self.audit.append(
            {
                "timestamp": utcnow(),
                "actor": context.actor,
                "tenant": context.tenant,
                "workspace": context.workspace,
                "action": action,
                "resource": resource,
                "advisory_only": True,
                "execution_authorized": False,
            }
        )

    def _add(
        self,
        store: dict[str, T],
        item: T,
        context: PredictiveContext,
        resource_type: str,
        metric: str | None = None,
    ) -> T:
        self._require(context)
        self._scoped(item, context)
        if item.id in store:
            raise ValueError(f"{resource_type} ID must be unique.")
        store[item.id] = item
        self.history.append(
            {"type": resource_type, **asdict(item)}  # type: ignore[call-overload]
        )
        if metric:
            self.metrics.increment(metric)
        self._record(context, f"{resource_type}.recorded", item.id)
        return item

    def create_profile(
        self, profile: PredictiveProfile, context: PredictiveContext
    ) -> PredictiveProfile:
        self._require(context)
        self._scoped(profile, context)
        profile.validate(
            max_history_days=self.max_history_days,
            max_horizon_days=self.max_horizon_days,
        )
        unknown = set(profile.sources) - set(self.sources)
        if unknown:
            raise ValueError(f"Unknown approved sources: {sorted(unknown)}")
        if profile.id in self.profiles:
            raise ValueError("Profile ID must be unique.")
        self.profiles[profile.id] = profile
        self.metrics.increment("tiktok_predictive_profiles_total")
        self._record(context, "profile.created", profile.id)
        return profile

    def collect(
        self, profile_id: str, context: PredictiveContext
    ) -> dict[str, tuple[dict[str, object], ...]]:
        self._require(context)
        profile = self.profiles[profile_id]
        self._scoped(profile, context)
        result: dict[str, tuple[dict[str, object], ...]] = {}
        for name in profile.sources:
            rows = self.sources[name].read_history(
                profile.history_start,
                profile.history_end,
                context,
                limit=self.max_results,
            )
            if len(rows) > self.max_results:
                raise ValueError("Source exceeded bounded result size.")
            if any(
                row.get("tenant") != context.tenant
                or row.get("workspace") != context.workspace
                for row in rows
            ):
                raise PermissionError("Adapter returned data outside scope.")
            result[name] = rows
        self._record(context, "history.collected", profile_id)
        return result

    def analyze_trend(
        self, item: TrendAnalysis, context: PredictiveContext
    ) -> TrendAnalysis:
        if item.direction not in TREND_DIRECTIONS:
            raise ValueError("Unsupported trend direction.")
        if item.observations < 2 or item.window_days < 1:
            raise ValueError("Trend analysis needs bounded historical observations.")
        if item.causal_claim:
            raise ValueError("Unsupported causal claims are forbidden.")
        validate_references(item.evidence_references)
        self._scoped(self.profiles[item.profile_id], context)
        return self._add(
            self.trends,
            item,
            context,
            "trend",
            "tiktok_predictive_trends_total",
        )

    def generate_forecast(self, item: Forecast, context: PredictiveContext) -> Forecast:
        started = perf_counter()
        profile = self.profiles[item.profile_id]
        self._scoped(profile, context)
        if (
            not 1
            <= item.horizon_days
            <= min(profile.horizon_days, self.max_horizon_days)
        ):
            raise ValueError("Forecast horizon exceeds profile bounds.")
        if not item.lower_bound <= item.predicted_value <= item.upper_bound:
            raise ValueError("Prediction must fall within its confidence range.")
        validate_ratio(item.confidence, "Confidence")
        validate_references(item.evidence_references)
        if not item.assumptions:
            raise ValueError("Forecast assumptions are required.")
        if not item.advisory_only or item.direct_execution:
            raise ValueError("Forecasts must remain advisory and non-executable.")
        result = self._add(
            self.forecasts,
            item,
            context,
            "forecast",
            "tiktok_predictive_forecasts_total",
        )
        self.metrics.observe("tiktok_predictive_confidence", item.confidence)
        self.metrics.observe(
            "tiktok_predictive_latency_seconds", perf_counter() - started
        )
        return result

    def compare_scenario(self, item: Scenario, context: PredictiveContext) -> Scenario:
        validate_ratio(item.risk_score, "Risk score")
        validate_ratio(item.confidence, "Confidence")
        if not item.assumptions:
            raise ValueError("Scenario assumptions are required.")
        self._scoped(self.profiles[item.profile_id], context)
        return self._add(self.scenarios, item, context, "scenario")

    def forecast_capacity(
        self, item: CapacityForecast, context: PredictiveContext
    ) -> CapacityForecast:
        validate_ratio(item.confidence, "Confidence")
        validate_references(item.evidence_references)
        if min(item.horizon_days, item.required_capacity, item.available_capacity) < 0:
            raise ValueError("Capacity values cannot be negative.")
        if abs(item.gap - (item.required_capacity - item.available_capacity)) > 1e-9:
            raise ValueError("Capacity gap is inconsistent.")
        self._scoped(self.profiles[item.profile_id], context)
        return self._add(self.capacity, item, context, "capacity")

    def forecast_risk(
        self, item: RiskForecast, context: PredictiveContext
    ) -> RiskForecast:
        validate_ratio(item.current_score, "Current risk")
        validate_ratio(item.predicted_score, "Predicted risk")
        validate_ratio(item.confidence, "Confidence")
        validate_references(item.evidence_references)
        if item.trend not in TREND_DIRECTIONS:
            raise ValueError("Unsupported risk trend.")
        self._scoped(self.profiles[item.profile_id], context)
        return self._add(self.risk, item, context, "risk")

    def estimate_confidence(
        self, item: ConfidenceEstimate, context: PredictiveContext
    ) -> ConfidenceEstimate:
        self._scoped(self.forecasts[item.forecast_id], context)
        for name in ("score", "data_quality", "stability", "calibration_error"):
            validate_ratio(float(getattr(item, name)), name)
        if item.sample_size < 2:
            raise ValueError("Confidence estimation requires at least two samples.")
        return self._add(self.confidence, item, context, "confidence")

    def recommend(
        self, item: PredictiveRecommendation, context: PredictiveContext
    ) -> PredictiveRecommendation:
        self._scoped(self.profiles[item.profile_id], context)
        validate_ratio(item.confidence, "Confidence")
        validate_references(item.evidence_references)
        if (
            not item.advisory_only
            or item.automatic_decision
            or item.direct_execution
            or item.runtime_change
            or item.publishing
        ):
            raise ValueError("Recommendations must remain advisory and reference-only.")
        return self._add(
            self.recommendations,
            item,
            context,
            "recommendation",
            "tiktok_predictive_recommendations_total",
        )

    def evaluate_forecast(
        self, item: ForecastEvaluation, context: PredictiveContext
    ) -> ForecastEvaluation:
        forecast = self.forecasts[item.forecast_id]
        self._scoped(forecast, context)
        expected_error = abs(item.actual_value - forecast.predicted_value)
        if abs(item.absolute_error - expected_error) > 1e-9:
            raise ValueError("Forecast evaluation error is inconsistent.")
        if item.percentage_error < 0 or "://" not in item.actual_value_reference:
            raise ValueError("Evaluation requires a valid reference and error.")
        return self._add(self.evaluations, item, context, "evaluation")

    def items(
        self,
        store: Mapping[str, object],
        context: PredictiveContext,
        *,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        self._require(context)
        bounded = self.max_results if limit is None else limit
        if not 1 <= bounded <= self.max_results:
            raise ValueError("Requested result size exceeds the configured bound.")
        result = []
        for item in store.values():
            if (
                getattr(item, "tenant", None) == context.tenant
                and getattr(item, "workspace", None) == context.workspace
            ):
                result.append(asdict(item))  # type: ignore[call-overload]
        return result[:bounded]

    def get_history(self, context: PredictiveContext) -> list[dict[str, Any]]:
        self._require(context)
        return [
            entry
            for entry in self.history
            if entry.get("tenant") == context.tenant
            and entry.get("workspace") == context.workspace
        ][: self.max_results]

    def analytics(self, context: PredictiveContext) -> dict[str, Any]:
        self._require(context)
        scoped_forecasts = self.items(self.forecasts, context)
        scoped_evaluations = self.items(self.evaluations, context)
        confidences = [float(item["confidence"]) for item in scoped_forecasts]
        errors = [float(item["absolute_error"]) for item in scoped_evaluations]
        return {
            "forecasts_total": len(scoped_forecasts),
            "trends_total": len(self.items(self.trends, context)),
            "scenarios_total": len(self.items(self.scenarios, context)),
            "capacity_forecasts_total": len(self.items(self.capacity, context)),
            "risk_forecasts_total": len(self.items(self.risk, context)),
            "recommendations_total": len(self.items(self.recommendations, context)),
            "evaluations_total": len(scoped_evaluations),
            "average_confidence": mean(confidences) if confidences else 0.0,
            "mean_absolute_error": mean(errors) if errors else 0.0,
            "advisory_only": True,
            "causal_claims": False,
        }

    def dashboard(self, context: PredictiveContext) -> dict[str, Any]:
        return {
            "forecast_overview": {
                **self.analytics(context),
                "direct_execution": False,
                "automatic_decisions": False,
                "runtime_changes": False,
                "publishing": False,
                "restriction_bypass": False,
            },
            "sections": (
                "Forecast Overview",
                "Trend Analysis",
                "Scenario Comparison",
                "Capacity Forecast",
                "Risk Forecast",
                "Confidence",
                "Recommendations",
                "Analytics",
                "History",
            ),
        }
