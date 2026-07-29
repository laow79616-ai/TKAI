"""Evidence-backed reasoning and advisory recommendations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from time import perf_counter
from typing import Any

from .adapters import (
    INTEGRATION_MODULES,
    ReadOnlyIntelligencePort,
    ReferenceOnlyIntelligencePort,
)
from .metrics import IntelligenceMetrics
from .models import (
    EvidenceItem,
    IntelligenceContext,
    IntelligenceProfile,
    Prediction,
    ReasoningResult,
    Recommendation,
    RecommendationPriority,
    validate_confidence,
)


class TikTokAutonomousIntelligenceCenter:
    """Aggregates and reasons over snapshots without executing or publishing."""

    def __init__(
        self, modules: Mapping[str, ReadOnlyIntelligencePort] | None = None
    ) -> None:
        supplied = modules or {}
        self.modules = {
            name: supplied.get(name, ReferenceOnlyIntelligencePort(name))
            for name in INTEGRATION_MODULES
        }
        self.profiles: dict[str, IntelligenceProfile] = {}
        self.reasoning_results: dict[str, ReasoningResult] = {}
        self.recommendations: dict[str, Recommendation] = {}
        self.predictions: dict[str, Prediction] = {}
        self.history: list[dict[str, Any]] = []
        self.audit: list[dict[str, Any]] = []
        self.metrics = IntelligenceMetrics()

    @staticmethod
    def _require(context: IntelligenceContext, action: str) -> None:
        required = f"tiktok:intelligence:{action}"
        if (
            required not in context.permissions
            and "tiktok:intelligence:admin" not in context.permissions
        ):
            raise PermissionError(f"RBAC permission required: {required}")

    @staticmethod
    def _scoped(item: object, context: IntelligenceContext) -> None:
        if (
            getattr(item, "tenant", None) != context.tenant
            or getattr(item, "workspace", None) != context.workspace
        ):
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _record(self, context: IntelligenceContext, action: str, resource: str) -> None:
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
        self, profile: IntelligenceProfile, context: IntelligenceContext
    ) -> IntelligenceProfile:
        self._require(context, "write")
        self._scoped(profile, context)
        profile.validate()
        unknown = set(profile.modules) - set(self.modules)
        if unknown:
            raise ValueError(f"Unknown bounded intelligence modules: {sorted(unknown)}")
        if profile.id in self.profiles:
            raise ValueError("Intelligence profile ID must be unique.")
        self.profiles[profile.id] = profile
        self.metrics.increment("tiktok_intelligence_profiles_total")
        self._record(context, "profile.created", profile.id)
        return profile

    def aggregate_context(
        self, profile_id: str, subject: str, context: IntelligenceContext
    ) -> tuple[EvidenceItem, ...]:
        self._require(context, "read")
        profile = self.profiles[profile_id]
        self._scoped(profile, context)
        if not subject:
            raise ValueError("A bounded intelligence subject is required.")
        evidence = []
        for module in profile.modules:
            snapshot = self.modules[module].read_snapshot(subject, context)
            if snapshot.get("tenant") != context.tenant:
                raise PermissionError("Adapter returned cross-tenant intelligence.")
            evidence.append(
                EvidenceItem(
                    module,
                    f"{module}://{subject}",
                    f"Read-only {module} snapshot available.",
                    f"integrity://{module}/{subject}",
                )
            )
        return tuple(evidence)

    def reason(
        self,
        reference: str,
        profile_id: str,
        question: str,
        context: IntelligenceContext,
        *,
        confidence: float,
        assumptions: tuple[str, ...] = (),
    ) -> ReasoningResult:
        self._require(context, "reason")
        validate_confidence(confidence)
        started = perf_counter()
        evidence = self.aggregate_context(profile_id, question, context)
        if not evidence:
            raise ValueError("Explainable reasoning requires evidence.")
        result = ReasoningResult(
            reference,
            profile_id,
            context.tenant,
            context.workspace,
            question,
            f"Reasoning synthesized {len(evidence)} bounded module snapshots.",
            evidence,
            confidence,
            assumptions,
        )
        self.reasoning_results[reference] = result
        self.history.append({"type": "reasoning", **asdict(result)})
        self.metrics.increment("tiktok_intelligence_reasoning_total")
        self.metrics.observe(
            "tiktok_intelligence_latency_seconds", perf_counter() - started
        )
        self._record(context, "reasoning.created", reference)
        return result

    def recommend(
        self,
        reference: str,
        reasoning_id: str,
        title: str,
        rationale: str,
        priority: RecommendationPriority,
        context: IntelligenceContext,
        *,
        confidence: float,
    ) -> Recommendation:
        self._require(context, "recommend")
        validate_confidence(confidence)
        reasoning = self.reasoning_results[reasoning_id]
        self._scoped(reasoning, context)
        item = Recommendation(
            reference,
            reasoning_id,
            context.tenant,
            context.workspace,
            title,
            rationale,
            priority,
            confidence,
            tuple(item.reference for item in reasoning.evidence),
        )
        self.recommendations[reference] = item
        self.history.append({"type": "recommendation", **asdict(item)})
        self.metrics.increment("tiktok_intelligence_recommendations_total")
        self._record(context, "recommendation.created", reference)
        return item

    def predict(
        self,
        reference: str,
        reasoning_id: str,
        subject: str,
        outcome: str,
        horizon_seconds: int,
        context: IntelligenceContext,
        *,
        confidence: float,
        assumptions: tuple[str, ...],
    ) -> Prediction:
        self._require(context, "predict")
        validate_confidence(confidence)
        if horizon_seconds <= 0 or not assumptions:
            raise ValueError("Predictions require a positive horizon and assumptions.")
        reasoning = self.reasoning_results[reasoning_id]
        self._scoped(reasoning, context)
        item = Prediction(
            reference,
            reasoning_id,
            context.tenant,
            context.workspace,
            subject,
            outcome,
            horizon_seconds,
            confidence,
            assumptions,
            tuple(item.reference for item in reasoning.evidence),
        )
        self.predictions[reference] = item
        self.history.append({"type": "prediction", **asdict(item)})
        self.metrics.increment("tiktok_intelligence_predictions_total")
        self._record(context, "prediction.created", reference)
        return item

    def _items(
        self, store: Mapping[str, object], context: IntelligenceContext
    ) -> list[dict[str, Any]]:
        self._require(context, "read")
        return [
            asdict(item)
            for item in store.values()
            if getattr(item, "tenant", None) == context.tenant
            and getattr(item, "workspace", None) == context.workspace
        ]

    def analytics(self, context: IntelligenceContext) -> dict[str, float]:
        return {
            "profiles_total": float(len(self._items(self.profiles, context))),
            "reasoning_total": float(len(self._items(self.reasoning_results, context))),
            "predictions_total": float(len(self._items(self.predictions, context))),
            "recommendations_total": float(
                len(self._items(self.recommendations, context))
            ),
            "latency_seconds": self.metrics.values[
                "tiktok_intelligence_latency_seconds"
            ],
        }

    def dashboard(self, context: IntelligenceContext) -> dict[str, Any]:
        return {
            "sections": [
                "intelligence_overview",
                "reasoning",
                "predictions",
                "recommendations",
                "evidence",
                "analytics",
                "history",
            ],
            "intelligence_overview": {
                "read_only": True,
                "direct_execution": False,
                "publishing": False,
                "integrations": list(self.modules),
            },
            "reasoning": self._items(self.reasoning_results, context),
            "predictions": self._items(self.predictions, context),
            "recommendations": self._items(self.recommendations, context),
            "analytics": self.analytics(context),
            "history": [
                item
                for item in self.history
                if item["tenant"] == context.tenant
                and item["workspace"] == context.workspace
            ],
        }
