"""Explainable, offline historical learning with advisory-only output."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from time import perf_counter
from typing import Any

from .adapters import (
    INTEGRATION_MODULES,
    ReadOnlyLearningPort,
    ReferenceOnlyLearningPort,
)
from .metrics import LearningMetrics
from .models import (
    HistoricalOutcome,
    LearningContext,
    LearningPattern,
    LearningProfile,
    LearningRecommendation,
    Lesson,
    validate_confidence,
)


class TikTokAutonomousLearningCenter:
    """Learns from immutable snapshots without changing runtime state."""

    def __init__(
        self, modules: Mapping[str, ReadOnlyLearningPort] | None = None
    ) -> None:
        supplied = modules or {}
        self.modules = {
            name: supplied.get(name, ReferenceOnlyLearningPort(name))
            for name in INTEGRATION_MODULES
        }
        self.profiles: dict[str, LearningProfile] = {}
        self.patterns: dict[str, LearningPattern] = {}
        self.lessons: dict[str, Lesson] = {}
        self.recommendations: dict[str, LearningRecommendation] = {}
        self.history: list[dict[str, Any]] = []
        self.audit: list[dict[str, str]] = []
        self.metrics = LearningMetrics()

    @staticmethod
    def _require(context: LearningContext, action: str) -> None:
        required = f"tiktok:learning:{action}"
        if (
            required not in context.permissions
            and "tiktok:learning:admin" not in context.permissions
        ):
            raise PermissionError(f"RBAC permission required: {required}")

    @staticmethod
    def _scoped(item: object, context: LearningContext) -> None:
        if (
            getattr(item, "tenant", None) != context.tenant
            or getattr(item, "workspace", None) != context.workspace
        ):
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _record(self, context: LearningContext, action: str, resource: str) -> None:
        self.audit.append(
            {
                "actor": context.actor,
                "tenant": context.tenant,
                "workspace": context.workspace,
                "action": action,
                "resource": resource,
            }
        )

    def create_profile(
        self, profile: LearningProfile, context: LearningContext
    ) -> LearningProfile:
        self._require(context, "manage")
        self._scoped(profile, context)
        profile.validate()
        unknown = set(profile.modules) - set(self.modules)
        if unknown:
            raise ValueError(f"Unknown bounded learning modules: {sorted(unknown)}")
        if profile.id in self.profiles:
            raise ValueError("Learning profile ID must be unique.")
        self.profiles[profile.id] = profile
        self.metrics.increment("tiktok_learning_profiles_total")
        self._record(context, "profile.created", profile.id)
        return profile

    def collect_dataset(
        self, profile_id: str, subject: str, context: LearningContext
    ) -> tuple[HistoricalOutcome, ...]:
        self._require(context, "analyze")
        profile = self.profiles[profile_id]
        self._scoped(profile, context)
        if not subject:
            raise ValueError("A bounded learning subject is required.")
        outcomes: list[HistoricalOutcome] = []
        for module in profile.modules:
            outcomes.extend(self.modules[module].read_history(subject, context))
        return tuple(outcomes)

    def discover_patterns(
        self, profile_id: str, subject: str, context: LearningContext
    ) -> tuple[LearningPattern, ...]:
        """Group repeated outcomes; this is deterministic bounded offline analysis."""
        started = perf_counter()
        profile = self.profiles[profile_id]
        dataset = self.collect_dataset(profile_id, subject, context)
        grouped: defaultdict[str, list[HistoricalOutcome]] = defaultdict(list)
        for item in dataset:
            grouped[item.outcome].append(item)
        discovered = []
        for outcome, samples in sorted(grouped.items()):
            if len(samples) < profile.minimum_samples:
                continue
            average = sum(item.score for item in samples) / len(samples)
            confidence = min(1.0, len(samples) / (profile.minimum_samples * 2))
            reference = f"{profile_id}:{subject}:{outcome}"
            pattern = LearningPattern(
                reference,
                profile_id,
                context.tenant,
                context.workspace,
                subject,
                outcome,
                len(samples),
                average,
                confidence,
                tuple(item.evidence_reference for item in samples),
                (
                    f"{outcome!r} recurred in {len(samples)} attributable historical "
                    f"outcomes with mean score {average:.3f}."
                ),
            )
            self.patterns[reference] = pattern
            self.history.append({"type": "pattern", **asdict(pattern)})
            self.metrics.increment("tiktok_learning_patterns_total")
            discovered.append(pattern)
        self.metrics.observe(
            "tiktok_learning_latency_seconds", perf_counter() - started
        )
        self._record(context, "patterns.discovered", profile_id)
        return tuple(discovered)

    def extract_lesson(
        self,
        reference: str,
        pattern_id: str,
        statement: str,
        context: LearningContext,
    ) -> Lesson:
        self._require(context, "analyze")
        pattern = self.patterns[pattern_id]
        self._scoped(pattern, context)
        if not statement:
            raise ValueError("An explainable lesson statement is required.")
        lesson = Lesson(
            reference,
            pattern_id,
            context.tenant,
            context.workspace,
            statement,
            pattern.confidence,
            pattern.evidence_references,
        )
        self.lessons[reference] = lesson
        self.history.append({"type": "lesson", **asdict(lesson)})
        self._record(context, "lesson.extracted", reference)
        return lesson

    def recommend(
        self,
        reference: str,
        lesson_id: str,
        title: str,
        rationale: str,
        context: LearningContext,
        *,
        confidence: float,
    ) -> LearningRecommendation:
        self._require(context, "recommend")
        validate_confidence(confidence)
        lesson = self.lessons[lesson_id]
        self._scoped(lesson, context)
        if confidence > lesson.confidence:
            raise ValueError("Recommendation confidence cannot exceed its lesson.")
        item = LearningRecommendation(
            reference,
            lesson_id,
            context.tenant,
            context.workspace,
            title,
            rationale,
            confidence,
            lesson.evidence_references,
        )
        self.recommendations[reference] = item
        self.history.append({"type": "recommendation", **asdict(item)})
        self.metrics.increment("tiktok_learning_recommendations_total")
        self._record(context, "recommendation.created", reference)
        return item

    def _items(
        self, store: Mapping[str, Any], context: LearningContext
    ) -> list[dict[str, Any]]:
        self._require(context, "read")
        return [
            asdict(item)
            for item in store.values()
            if getattr(item, "tenant", None) == context.tenant
            and getattr(item, "workspace", None) == context.workspace
        ]

    def evaluate(
        self, pattern_ids: Sequence[str], context: LearningContext
    ) -> dict[str, float]:
        self._require(context, "read")
        patterns = [self.patterns[item] for item in pattern_ids]
        for pattern in patterns:
            self._scoped(pattern, context)
        return {
            "patterns_total": float(len(patterns)),
            "mean_confidence": (
                sum(item.confidence for item in patterns) / len(patterns)
                if patterns
                else 0.0
            ),
            "mean_outcome_score": (
                sum(item.average_score for item in patterns) / len(patterns)
                if patterns
                else 0.0
            ),
        }

    def analytics(self, context: LearningContext) -> dict[str, float]:
        patterns = self._items(self.patterns, context)
        return {
            "profiles_total": float(len(self._items(self.profiles, context))),
            "patterns_total": float(len(patterns)),
            "lessons_total": float(len(self._items(self.lessons, context))),
            "recommendations_total": float(
                len(self._items(self.recommendations, context))
            ),
            "mean_confidence": (
                sum(float(item["confidence"]) for item in patterns) / len(patterns)
                if patterns
                else 0.0
            ),
            "latency_seconds": self.metrics.values[
                "tiktok_learning_latency_seconds"
            ],
        }

    def dashboard(self, context: LearningContext) -> dict[str, Any]:
        self._require(context, "read")
        return {
            "sections": [
                "learning_overview",
                "patterns",
                "lessons",
                "recommendations",
                "analytics",
                "history",
            ],
            "learning_overview": {
                "offline_analysis": True,
                "read_only_integrations": True,
                "direct_runtime_configuration": False,
                "direct_execution": False,
                "publishing": False,
                "restriction_bypass": False,
                "integrations": list(self.modules),
            },
            "patterns": self._items(self.patterns, context),
            "lessons": self._items(self.lessons, context),
            "recommendations": self._items(self.recommendations, context),
            "analytics": self.analytics(context),
            "history": [
                item
                for item in self.history
                if item["tenant"] == context.tenant
                and item["workspace"] == context.workspace
            ],
        }
