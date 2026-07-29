"""Read-only analysis and advisory recommendations for historical decisions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, replace
from statistics import mean
from time import perf_counter
from typing import Any, Protocol, TypeVar

from .adapters import (
    DECISION_SOURCES,
    ReadOnlyDecisionSource,
    ReferenceOnlyDecisionSource,
    ReferenceOnlyHandoff,
)
from .metrics import DecisionEvolutionMetrics
from .models import (
    ALLOWED_TRANSITIONS,
    ConfidenceAnalysis,
    DecisionBaseline,
    DecisionComparison,
    DecisionEvaluation,
    DecisionEvolutionContext,
    DecisionEvolutionProfile,
    DecisionLesson,
    DecisionOutcome,
    DecisionPattern,
    DecisionRecord,
    DecisionReview,
    EvolutionRecommendation,
    ProfileStatus,
    ScoreComponent,
    VersionRecord,
    utcnow,
    validate_ratio,
    validate_references,
)


class IdentifiedRecord(Protocol):
    @property
    def id(self) -> str: ...


T = TypeVar("T", bound=IdentifiedRecord)

PATTERN_TYPES = frozenset(
    {
        "successful_decision",
        "failed_decision",
        "delayed_decision",
        "overconfident",
        "underconfident",
        "approval_bottleneck",
        "evidence_gap",
        "risk_underestimation",
        "resource_estimation_error",
        "schedule_estimation_error",
        "recovery_selection",
    }
)
COMPARISON_TYPES = frozenset(
    {
        "expected_vs_observed",
        "decision_vs_baseline",
        "strategy",
        "mission",
        "risk",
        "recovery",
        "resource_estimate",
        "schedule_estimate",
        "confidence_calibration",
    }
)
RECOMMENDATION_TYPES = frozenset(
    {
        "decision_process",
        "evidence",
        "risk_evaluation",
        "confidence_calibration",
        "approval_workflow",
        "resource_estimation",
        "schedule_estimation",
        "recovery_selection",
    }
)


class TikTokDecisionEvolutionCenter:
    """Improves decision quality without approval or operational authority."""

    def __init__(
        self,
        sources: Mapping[str, ReadOnlyDecisionSource] | None = None,
        *,
        max_range_days: int = 366,
        max_results: int = 500,
    ) -> None:
        if not 1 <= max_range_days <= 3_650 or not 1 <= max_results <= 1_000:
            raise ValueError("Analysis bounds are outside supported limits.")
        supplied = sources or {}
        self.sources = {
            name: supplied.get(name, ReferenceOnlyDecisionSource(name))
            for name in DECISION_SOURCES
        }
        self.max_range_days = max_range_days
        self.max_results = max_results
        self.profiles: dict[str, DecisionEvolutionProfile] = {}
        self.decisions: dict[str, DecisionRecord] = {}
        self.outcomes: dict[str, DecisionOutcome] = {}
        self.baselines: dict[str, DecisionBaseline] = {}
        self.patterns: dict[str, DecisionPattern] = {}
        self.comparisons: dict[str, DecisionComparison] = {}
        self.evaluations: dict[str, DecisionEvaluation] = {}
        self.confidence: dict[str, ConfidenceAnalysis] = {}
        self.lessons: dict[str, DecisionLesson] = {}
        self.recommendations: dict[str, EvolutionRecommendation] = {}
        self.reviews: dict[str, DecisionReview] = {}
        self.versions: dict[str, VersionRecord] = {}
        self.history: list[dict[str, Any]] = []
        self.audit: list[dict[str, Any]] = []
        self.metrics = DecisionEvolutionMetrics()

    @staticmethod
    def _require(context: DecisionEvolutionContext, action: str) -> None:
        required = f"tiktok:decision-evolution:{action}"
        if (
            required not in context.permissions
            and "tiktok:decision-evolution:admin" not in context.permissions
        ):
            raise PermissionError(f"RBAC permission required: {required}")

    @staticmethod
    def _scoped(item: object, context: DecisionEvolutionContext) -> None:
        if (
            getattr(item, "tenant", None) != context.tenant
            or getattr(item, "workspace", None) != context.workspace
        ):
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _record(
        self,
        context: DecisionEvolutionContext,
        action: str,
        resource: str,
        *,
        approval_authorizes_execution: bool = False,
    ) -> None:
        self.audit.append(
            {
                "timestamp": utcnow(),
                "actor": context.actor,
                "tenant": context.tenant,
                "workspace": context.workspace,
                "action": action,
                "resource": resource,
                "approval_authorizes_execution": approval_authorizes_execution,
            }
        )

    def _add(
        self,
        store: dict[str, T],
        item: T,
        context: DecisionEvolutionContext,
        resource_type: str,
        metric: str | None = None,
        *,
        action: str = "analyze",
    ) -> T:
        self._require(context, action)
        self._scoped(item, context)
        item_id = str(item.id)
        if item_id in store:
            raise ValueError(f"{resource_type} ID must be unique.")
        store[item_id] = item
        self.history.append(
            {"type": resource_type, **asdict(item)}  # type: ignore[call-overload]
        )
        if metric:
            self.metrics.increment(metric)
        self._record(context, f"{resource_type}.recorded", item_id)
        return item

    def create_profile(
        self,
        profile: DecisionEvolutionProfile,
        context: DecisionEvolutionContext,
    ) -> DecisionEvolutionProfile:
        self._require(context, "analyze")
        self._scoped(profile, context)
        profile.validate(max_range_days=self.max_range_days)
        unknown = set(profile.scope) - set(self.sources)
        if unknown:
            raise ValueError(f"Unknown bounded decision sources: {sorted(unknown)}")
        if profile.id in self.profiles:
            raise ValueError("Profile ID must be unique.")
        self.profiles[profile.id] = profile
        self.metrics.increment("tiktok_decision_evolution_profiles_total")
        self._record(context, "profile.created", profile.id)
        return profile

    def transition_profile(
        self,
        profile_id: str,
        status: ProfileStatus,
        context: DecisionEvolutionContext,
    ) -> DecisionEvolutionProfile:
        self._require(context, "review")
        profile = self.profiles[profile_id]
        self._scoped(profile, context)
        if status not in ALLOWED_TRANSITIONS[profile.status]:
            raise ValueError(
                f"Invalid lifecycle transition: {profile.status} -> {status}"
            )
        profile.status = status
        profile.version += 1
        self._record(
            context,
            "profile.status_changed",
            profile_id,
            approval_authorizes_execution=False,
        )
        return profile

    def collect(
        self,
        profile_id: str,
        context: DecisionEvolutionContext,
    ) -> dict[str, tuple[dict[str, object], ...]]:
        self._require(context, "read")
        profile = self.profiles[profile_id]
        self._scoped(profile, context)
        result: dict[str, tuple[dict[str, object], ...]] = {}
        for source_name in profile.scope:
            rows = self.sources[source_name].read_decisions(
                profile.time_range_start,
                profile.time_range_end,
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
            result[source_name] = rows
        self._record(context, "sources.collected", profile_id)
        return result

    def record_decision(
        self, item: DecisionRecord, context: DecisionEvolutionContext
    ) -> DecisionRecord:
        validate_ratio(item.confidence, "Confidence")
        validate_references(item.evidence_references)
        profile = self.profiles[item.profile_id]
        self._scoped(profile, context)
        if not profile.time_range_start <= item.timestamp <= profile.time_range_end:
            raise ValueError("Decision timestamp is outside the profile time range.")
        return self._add(
            self.decisions,
            item,
            context,
            "decision",
            "tiktok_decision_evolution_decisions_total",
        )

    def record_outcome(
        self, item: DecisionOutcome, context: DecisionEvolutionContext
    ) -> DecisionOutcome:
        self._scoped(self.decisions[item.decision_id], context)
        validate_references(item.evidence_references)
        if item.latency_seconds < 0:
            raise ValueError("Outcome latency cannot be negative.")
        return self._add(
            self.outcomes,
            item,
            context,
            "outcome",
            "tiktok_decision_evolution_outcomes_total",
        )

    def record_baseline(
        self, item: DecisionBaseline, context: DecisionEvolutionContext
    ) -> DecisionBaseline:
        for name in (
            "historical_decision_quality",
            "historical_success_rate",
            "historical_failure_rate",
            "historical_recovery_rate",
            "historical_confidence",
            "historical_risk",
        ):
            validate_ratio(float(getattr(item, name)), name)
        if item.rolling_window_days < 1 or item.historical_approval_time < 0:
            raise ValueError("Baseline windows and approval time must be non-negative.")
        return self._add(self.baselines, item, context, "baseline")

    def identify_pattern(
        self, item: DecisionPattern, context: DecisionEvolutionContext
    ) -> DecisionPattern:
        if item.pattern_type not in PATTERN_TYPES:
            raise ValueError("Unsupported decision pattern.")
        if item.causal_claim:
            raise ValueError("Unsupported causal claims are forbidden.")
        if item.support_count < 1:
            raise ValueError("Patterns require supporting observations.")
        validate_references(item.evidence_references)
        return self._add(
            self.patterns,
            item,
            context,
            "pattern",
            "tiktok_decision_evolution_patterns_total",
        )

    def compare(
        self, item: DecisionComparison, context: DecisionEvolutionContext
    ) -> DecisionComparison:
        if item.comparison_type not in COMPARISON_TYPES or not item.explanation:
            raise ValueError("A supported, explainable comparison is required.")
        if round(item.observed_value - item.expected_value, 6) != round(
            item.difference, 6
        ):
            raise ValueError("Comparison difference is inconsistent.")
        return self._add(self.comparisons, item, context, "comparison")

    def evaluate(
        self,
        evaluation_id: str,
        decision_id: str,
        components: Mapping[str, tuple[float, float, str]],
        context: DecisionEvolutionContext,
    ) -> DecisionEvaluation:
        self._require(context, "analyze")
        started = perf_counter()
        decision = self.decisions[decision_id]
        self._scoped(decision, context)
        expected = (
            "evidence_completeness",
            "constraint_compliance",
            "risk_calibration",
            "confidence_calibration",
            "outcome_accuracy",
            "resource_estimate_accuracy",
            "schedule_accuracy",
            "recovery_appropriateness",
            "approval_efficiency",
        )
        if set(components) != set(expected):
            raise ValueError("Every explainable score component is required.")
        breakdown = tuple(
            ScoreComponent(name, *components[name]) for name in expected
        )
        for component in breakdown:
            validate_ratio(component.score, component.name)
            if component.weight <= 0 or not component.explanation:
                raise ValueError("Score weights and explanations are required.")
        total_weight = sum(component.weight for component in breakdown)
        quality = sum(
            component.score * component.weight for component in breakdown
        ) / total_weight
        values = {component.name: component.score for component in breakdown}
        item = DecisionEvaluation(
            evaluation_id,
            decision_id,
            context.tenant,
            context.workspace,
            quality,
            values["evidence_completeness"],
            values["constraint_compliance"],
            values["risk_calibration"],
            values["confidence_calibration"],
            values["outcome_accuracy"],
            values["resource_estimate_accuracy"],
            values["schedule_accuracy"],
            values["recovery_appropriateness"],
            values["approval_efficiency"],
            breakdown,
        )
        self._add(self.evaluations, item, context, "evaluation")
        self.metrics.observe("tiktok_decision_evolution_quality_score", quality)
        self.metrics.observe(
            "tiktok_decision_evolution_confidence_calibration",
            item.confidence_calibration,
        )
        self.metrics.observe(
            "tiktok_decision_evolution_evidence_completeness",
            item.evidence_completeness,
        )
        self.metrics.observe(
            "tiktok_decision_evolution_analysis_seconds", perf_counter() - started
        )
        return item

    def analyze_confidence(
        self,
        analysis_id: str,
        decision_id: str,
        observed_accuracy_reference: str,
        observed_accuracy: float,
        distribution: tuple[float, ...],
        context: DecisionEvolutionContext,
    ) -> ConfidenceAnalysis:
        decision = self.decisions[decision_id]
        self._scoped(decision, context)
        validate_ratio(observed_accuracy, "Observed accuracy")
        for value in distribution:
            validate_ratio(value, "Confidence distribution value")
        difference = observed_accuracy - decision.confidence
        trend = "calibrated" if abs(difference) <= 0.05 else (
            "underconfident" if difference > 0 else "overconfident"
        )
        item = ConfidenceAnalysis(
            analysis_id,
            decision_id,
            context.tenant,
            context.workspace,
            decision.confidence,
            observed_accuracy_reference,
            observed_accuracy,
            difference,
            trend,
            distribution,
            f"Observed accuracy differs from original confidence by {difference:+.3f}.",
        )
        return self._add(self.confidence, item, context, "confidence")

    def record_lesson(
        self, item: DecisionLesson, context: DecisionEvolutionContext
    ) -> DecisionLesson:
        if not item.improvement_summary:
            raise ValueError("Lessons require an improvement summary.")
        return self._add(self.lessons, item, context, "lesson")

    def recommend(
        self,
        recommendation_id: str,
        decision_id: str,
        recommendation_type: str,
        summary: str,
        rationale: str,
        evidence_references: tuple[str, ...],
        context: DecisionEvolutionContext,
        *,
        handoffs: tuple[str, ...] = (),
    ) -> EvolutionRecommendation:
        if recommendation_type not in RECOMMENDATION_TYPES:
            raise ValueError("Unsupported recommendation type.")
        if not summary or not rationale:
            raise ValueError("Recommendation summary and rationale are required.")
        validate_references(evidence_references)
        self._scoped(self.decisions[decision_id], context)
        refs = {
            destination: ReferenceOnlyHandoff.create(
                destination, recommendation_id
            )
            for destination in handoffs
        }
        item = EvolutionRecommendation(
            recommendation_id,
            decision_id,
            context.tenant,
            context.workspace,
            recommendation_type,
            summary,
            rationale,
            evidence_references,
            refs.get("knowledge_evolution"),
            refs.get("learning_center"),
            refs.get("governance_center"),
        )
        return self._add(
            self.recommendations,
            item,
            context,
            "recommendation",
            "tiktok_decision_evolution_recommendations_total",
        )

    def review(
        self, item: DecisionReview, context: DecisionEvolutionContext
    ) -> DecisionReview:
        self._require(context, "review")
        if not item.reviewer or not item.audit_reference:
            raise ValueError("Reviewer and audit reference are required.")
        result = self._add(
            self.reviews,
            item,
            context,
            "review",
            "tiktok_decision_evolution_reviews_total",
            action="review",
        )
        self._record(
            context,
            "analysis.approved_reference" if item.status == "approved" else "reviewed",
            item.id,
            approval_authorizes_execution=False,
        )
        return result

    def version(
        self,
        version_id: str,
        resource_type: str,
        resource_id: str,
        change_history: tuple[str, ...],
        context: DecisionEvolutionContext,
    ) -> VersionRecord:
        existing = [
            item
            for item in self.versions.values()
            if item.resource_type == resource_type
            and item.resource_id == resource_id
            and item.tenant == context.tenant
            and item.workspace == context.workspace
        ]
        item = VersionRecord(
            version_id,
            resource_type,
            resource_id,
            context.tenant,
            context.workspace,
            len(existing) + 1,
            utcnow(),
            None,
            change_history,
        )
        if existing:
            previous = max(existing, key=lambda value: value.version)
            self.versions[previous.id] = replace(previous, superseded_by=version_id)
        return self._add(self.versions, item, context, "version")

    def items(
        self,
        store: Mapping[str, Any],
        context: DecisionEvolutionContext,
        *,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        self._require(context, "read")
        bounded_limit = self.max_results if limit is None else limit
        if not 1 <= bounded_limit <= self.max_results:
            raise ValueError("Requested result size exceeds the configured bound.")
        return [
            asdict(item)
            for item in store.values()
            if getattr(item, "tenant", None) == context.tenant
            and getattr(item, "workspace", None) == context.workspace
        ][:bounded_limit]

    def get_history(
        self, context: DecisionEvolutionContext, *, limit: int | None = None
    ) -> list[dict[str, Any]]:
        self._require(context, "read")
        bounded_limit = self.max_results if limit is None else limit
        if not 1 <= bounded_limit <= self.max_results:
            raise ValueError("Requested history size exceeds the configured bound.")
        return [
            item
            for item in self.history
            if item["tenant"] == context.tenant
            and item["workspace"] == context.workspace
        ][-bounded_limit:]

    def analytics(self, context: DecisionEvolutionContext) -> dict[str, float]:
        evaluations = self.items(self.evaluations, context)
        decisions = self.items(self.decisions, context)
        outcomes = self.items(self.outcomes, context)
        confidence = self.items(self.confidence, context)
        reviews = self.items(self.reviews, context)
        success = sum(item["outcome_status"] == "success" for item in outcomes)
        failed = sum(item["outcome_status"] == "failed" for item in outcomes)
        return {
            "profiles_total": float(len(self.items(self.profiles, context))),
            "decisions_evaluated": float(len(evaluations)),
            "outcomes_evaluated": float(len(outcomes)),
            "patterns_identified": float(len(self.items(self.patterns, context))),
            "recommendations_generated": float(
                len(self.items(self.recommendations, context))
            ),
            "reviews_completed": float(
                sum(item["status"] == "completed" for item in reviews)
            ),
            "average_decision_quality": (
                mean(item["decision_quality_score"] for item in evaluations)
                if evaluations
                else 0.0
            ),
            "average_confidence_calibration": (
                mean(abs(item["calibration_difference"]) for item in confidence)
                if confidence
                else 0.0
            ),
            "average_approval_time": 0.0,
            "decision_success_rate": success / len(outcomes) if outcomes else 0.0,
            "decision_failure_rate": failed / len(outcomes) if outcomes else 0.0,
            "evidence_completeness_rate": (
                mean(item["evidence_completeness"] for item in evaluations)
                if evaluations
                else 0.0
            ),
            "risk_calibration_trend": (
                mean(item["risk_calibration"] for item in evaluations)
                if evaluations
                else 0.0
            ),
            "resource_accuracy_trend": (
                mean(item["resource_estimate_accuracy"] for item in evaluations)
                if evaluations
                else 0.0
            ),
            "schedule_accuracy_trend": (
                mean(item["schedule_accuracy"] for item in evaluations)
                if evaluations
                else 0.0
            ),
            "decisions_total": float(len(decisions)),
        }

    def dashboard(self, context: DecisionEvolutionContext) -> dict[str, Any]:
        stores: dict[str, Mapping[str, Any]] = {
            "profiles": self.profiles,
            "decisions": self.decisions,
            "outcomes": self.outcomes,
            "baselines": self.baselines,
            "patterns": self.patterns,
            "comparisons": self.comparisons,
            "evaluations": self.evaluations,
            "confidence": self.confidence,
            "lessons": self.lessons,
            "recommendations": self.recommendations,
            "reviews": self.reviews,
            "versions": self.versions,
        }
        return {
            "sections": [
                "decision_evolution_overview",
                *stores,
                "history",
                "analytics",
            ],
            "decision_evolution_overview": {
                "advisory_only": True,
                "automatic_approval": False,
                "direct_execution": False,
                "publishing": False,
                "outreach": False,
                "runtime_configuration_change": False,
                "restriction_circumvention": False,
                "captcha_bypass": False,
                "security_bypass": False,
                "kill_switch_aware": True,
                "workspace_pause_aware": True,
                "account_pause_aware": True,
            },
            **{name: self.items(store, context) for name, store in stores.items()},
            "history": self.get_history(context),
            "analytics": self.analytics(context),
        }
