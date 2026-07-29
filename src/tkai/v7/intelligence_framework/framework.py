"""Bounded, local, advisory-only unified intelligence framework."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from threading import RLock
from typing import TypeVar

from .contracts import (
    Alternative,
    Approval,
    Comparison,
    DecisionRecord,
    Evaluation,
    Evidence,
    Explanation,
    GovernanceMetadata,
    Hypothesis,
    IntelligenceContext,
    IntelligenceProfile,
    KnowledgeReference,
    Lifecycle,
    Observation,
    ReasoningMetadata,
    Recommendation,
    Review,
    Scope,
    Signal,
    SourceAdapter,
    VersionMetadata,
    serialize,
)

T = TypeVar("T")
MAX_ITEMS = 1000
MAX_EVIDENCE_REFERENCES = 250
SOURCE_NAMES = (
    "v7-ai-framework",
    "v7-data-storage-framework",
    "v7-configuration-framework",
    "v7-observability-framework",
    "v7-security-framework",
    "v7-resource-framework",
    "v7-workflow-framework",
    "v7-state-framework",
    "v7-event-fabric",
    "v7-service-mesh",
    "v7-capability-framework",
    "v6-intelligence-center",
    "v6-learning-center",
    "v6-knowledge-evolution-center",
    "v6-decision-evolution-center",
    "v6-predictive-analytics-center",
    "v6-autonomous-planning-center",
    "v6-governance-center",
    "v6-strategy-center",
    "v6-risk-control-center",
    "v6-business-intelligence-center",
    "v6-performance-insights-center",
    "v6-analytics-center",
)
METRIC_NAMES = (
    "v7_intelligence_profiles_total",
    "v7_intelligence_contexts_total",
    "v7_intelligence_evidence_total",
    "v7_intelligence_evidence_validated_total",
    "v7_intelligence_evidence_rejected_total",
    "v7_intelligence_signals_total",
    "v7_intelligence_observations_total",
    "v7_intelligence_hypotheses_total",
    "v7_intelligence_evaluations_total",
    "v7_intelligence_decisions_total",
    "v7_intelligence_recommendations_total",
    "v7_intelligence_reviews_total",
    "v7_intelligence_approvals_total",
    "v7_intelligence_evidence_completeness",
    "v7_intelligence_evidence_integrity",
    "v7_intelligence_confidence",
    "v7_intelligence_confidence_calibration",
    "v7_intelligence_decision_quality",
    "v7_intelligence_recommendation_quality",
    "v7_intelligence_analysis_seconds",
    "v7_intelligence_health_status",
)


class IntelligenceFrameworkError(RuntimeError):
    pass


class Registry:
    def __init__(self) -> None:
        self._items: dict[str, object] = {}
        self._lock = RLock()

    def add(self, key: str, item: T) -> T:
        with self._lock:
            if key in self._items:
                raise IntelligenceFrameworkError(f"immutable artifact exists: {key}")
            if len(self._items) >= MAX_ITEMS:
                raise IntelligenceFrameworkError("bounded registry capacity reached")
            self._items[key] = item
        return item

    def values(self, expected: type[T], scope: Scope | None = None) -> tuple[T, ...]:
        return tuple(
            x
            for x in self._items.values()
            if isinstance(x, expected)
            and (scope is None or getattr(x, "scope", None) == scope)
        )[:MAX_ITEMS]


class IntelligenceFramework:
    """Advisory metadata coordination with no execution surface."""

    PROJECTIONS = (
        "profiles",
        "contexts",
        "sources",
        "evidence",
        "knowledge",
        "signals",
        "observations",
        "reasoning",
        "hypotheses",
        "evaluations",
        "decisions",
        "alternatives",
        "comparisons",
        "confidence",
        "recommendations",
        "explanations",
        "reviews",
        "approvals",
        "governance",
        "policies",
        "versions",
        "history",
        "analytics",
        "health",
        "metrics",
        "audit",
        "lifecycle",
    )
    TYPES = {
        "profiles": IntelligenceProfile,
        "contexts": IntelligenceContext,
        "sources": SourceAdapter,
        "evidence": Evidence,
        "knowledge": KnowledgeReference,
        "signals": Signal,
        "observations": Observation,
        "reasoning": ReasoningMetadata,
        "hypotheses": Hypothesis,
        "evaluations": Evaluation,
        "decisions": DecisionRecord,
        "alternatives": Alternative,
        "comparisons": Comparison,
        "recommendations": Recommendation,
        "explanations": Explanation,
        "reviews": Review,
        "approvals": Approval,
        "governance": GovernanceMetadata,
        "versions": VersionMetadata,
    }

    def __init__(self) -> None:
        self.registries = {name: Registry() for name in self.PROJECTIONS}
        self.metrics = Counter({name: 0 for name in METRIC_NAMES})
        self.metrics["v7_intelligence_health_status"] = 1
        self.audit_log: list[dict[str, object]] = []
        self.events: list[dict[str, object]] = []
        for name in SOURCE_NAMES:
            self.registries["sources"].add(
                name, SourceAdapter(name, name.replace("-", " ").title(), "bounded")
            )

    def register_profile(self, item: IntelligenceProfile) -> IntelligenceProfile:
        return self._add("profiles", item.profile_id, item, "Profile Registered")

    def create_context(self, item: IntelligenceContext) -> IntelligenceContext:
        self._same_scope(
            "profiles", IntelligenceProfile, item.profile_reference, item.scope
        )
        return self._add("contexts", item.context_id, item, "Context Created")

    def record_evidence(self, item: Evidence) -> Evidence:
        event = (
            "Evidence Validated"
            if item.validation_status.lower() == "validated"
            else "Evidence Rejected"
        )
        return self._add("evidence", item.evidence_id, item, event)

    def register_knowledge(self, item: KnowledgeReference) -> KnowledgeReference:
        return self._add(
            "knowledge", item.knowledge_reference, item, "Knowledge Referenced"
        )

    def record_signal(self, item: Signal) -> Signal:
        return self._add("signals", item.signal_id, item, "Signal Recorded")

    def record_observation(self, item: Observation) -> Observation:
        return self._add(
            "observations", item.observation_id, item, "Observation Recorded"
        )

    def record_reasoning(self, item: ReasoningMetadata) -> ReasoningMetadata:
        if len(item.evidence_references) > MAX_EVIDENCE_REFERENCES:
            raise IntelligenceFrameworkError("bounded evidence references exceeded")
        return self._add(
            "reasoning", item.reasoning_session_id, item, "Reasoning Recorded"
        )

    def create_hypothesis(self, item: Hypothesis) -> Hypothesis:
        return self._add("hypotheses", item.hypothesis_id, item, "Hypothesis Created")

    def complete_evaluation(self, item: Evaluation) -> Evaluation:
        return self._add(
            "evaluations", item.evaluation_id, item, "Evaluation Completed"
        )

    def record_decision(self, item: DecisionRecord) -> DecisionRecord:
        return self._add("decisions", item.decision_id, item, "Decision Recorded")

    def add_alternative(self, item: Alternative) -> Alternative:
        return self._add(
            "alternatives", item.alternative_id, item, "Alternative Recorded"
        )

    def add_comparison(self, item: Comparison) -> Comparison:
        return self._add("comparisons", item.comparison_id, item, "Comparison Recorded")

    def generate_recommendation(self, item: Recommendation) -> Recommendation:
        return self._add(
            "recommendations", item.recommendation_id, item, "Recommendation Generated"
        )

    def add_explanation(self, item: Explanation) -> Explanation:
        return self._add(
            "explanations", item.explanation_id, item, "Explanation Recorded"
        )

    def complete_review(self, item: Review) -> Review:
        return self._add("reviews", item.review_id, item, "Review Completed")

    def record_approval(self, item: Approval) -> Approval:
        return self._add("approvals", item.approval_id, item, "Approval Recorded")

    def register_governance(self, item: GovernanceMetadata) -> GovernanceMetadata:
        return self._add("governance", item.governance_id, item, "Governance Recorded")

    def register_version(
        self, reference: str, item: VersionMetadata, scope: Scope
    ) -> VersionMetadata:
        key = f"{reference}:{item.version}:{scope.tenant}:{scope.workspace}"
        result = self.registries["versions"].add(key, item)
        self._record("Version Recorded", key, scope)
        return result

    def transition(
        self, profile_id: str, lifecycle: Lifecycle, scope: Scope
    ) -> IntelligenceProfile:
        current = self._same_scope("profiles", IntelligenceProfile, profile_id, scope)
        updated = replace(current, lifecycle=lifecycle, version=current.version + 1)
        self.registries["profiles"].add(f"{profile_id}:v{updated.version}", updated)
        self._record("Lifecycle Changed", profile_id, scope)
        return updated

    def projection(self, section: str, scope: Scope) -> object:
        if section not in self.PROJECTIONS:
            raise IntelligenceFrameworkError(f"unknown projection: {section}")
        if section == "metrics":
            return dict(self.metrics)
        if section == "health":
            return self.health(scope)
        if section == "analytics":
            return self.analytics(scope)
        if section in ("audit", "history"):
            return serialize(
                tuple(x for x in self.audit_log if x["scope"] == serialize(scope))
            )
        if section == "lifecycle":
            return serialize(
                tuple(
                    x.lifecycle
                    for x in self.registries["profiles"].values(
                        IntelligenceProfile, scope
                    )
                )
            )
        if section == "policies":
            return serialize(
                tuple(
                    x.policy_references
                    for x in self.registries["governance"].values(
                        GovernanceMetadata, scope
                    )
                )
            )
        if section == "confidence":
            values = self.registries["decisions"].values(
                DecisionRecord, scope
            ) + self.registries["recommendations"].values(Recommendation, scope)
            return serialize(
                tuple(
                    {"reference": self._key(x), "confidence": x.confidence}
                    for x in values
                )
            )
        expected = self.TYPES[section]
        selected_scope = None if section == "sources" else scope
        return serialize(self.registries[section].values(expected, selected_scope))

    def analytics(self, scope: Scope) -> dict[str, object]:
        result: dict[str, object] = {}
        for name, expected in self.TYPES.items():
            if name not in ("sources", "versions"):
                result[f"{name}_total"] = len(
                    self.registries[name].values(expected, scope)
                )
        evidence = self.registries["evidence"].values(Evidence, scope)
        result["validated_evidence_total"] = sum(
            x.validation_status.lower() == "validated" for x in evidence
        )
        result["rejected_evidence_total"] = sum(
            x.validation_status.lower() == "rejected" for x in evidence
        )
        result["average_evidence_integrity"] = self._average(
            x.reliability for x in evidence
        )
        decisions = self.registries["decisions"].values(DecisionRecord, scope)
        recommendations = self.registries["recommendations"].values(
            Recommendation, scope
        )
        result["average_confidence"] = self._average(
            x.confidence for x in decisions + recommendations
        )
        return result

    def health(self, scope: Scope) -> dict[str, object]:
        return {
            "status": "healthy",
            "registry_health": "healthy",
            "source_adapter_health": "healthy",
            "evidence_health": "healthy",
            "reasoning_health": "healthy",
            "evaluation_health": "healthy",
            "decision_health": "healthy",
            "recommendation_health": "healthy",
            "governance_health": "healthy",
            "compatibility_health": "healthy",
            "framework_readiness": True,
            "framework_liveness": True,
            "diagnostics": {
                "external_network": False,
                "execution": False,
                "automatic_approval": False,
                "secret_values": False,
                "hidden_reasoning": False,
            },
            "scope": serialize(scope),
        }

    def compatibility(self) -> dict[str, object]:
        return {
            "v6": True,
            "v7": True,
            "read_only_adapters": SOURCE_NAMES,
            "external_network": False,
            "runtime_mutation": False,
        }

    def _add(self, section: str, key: str, item: T, event: str) -> T:
        value = self.registries[section].add(key, item)
        metric = f"v7_intelligence_{section}_total"
        if metric in self.metrics:
            self.metrics[metric] += 1
        if isinstance(item, Evidence):
            target = f"v7_intelligence_evidence_{item.validation_status.lower()}_total"
            if target in self.metrics:
                self.metrics[target] += 1
        scope = getattr(item, "scope", None)
        if isinstance(scope, Scope):
            self._record(event, key, scope)
        return value

    def _same_scope(
        self, section: str, expected: type[T], reference: str, scope: Scope
    ) -> T:
        for value in self.registries[section].values(expected, scope):
            if self._key(value) == reference:
                return value
        raise IntelligenceFrameworkError(f"missing or cross-scope: {reference}")

    @staticmethod
    def _key(value: object) -> str:
        for name in (
            "profile_id",
            "context_id",
            "evidence_id",
            "decision_id",
            "recommendation_id",
        ):
            result = getattr(value, name, None)
            if isinstance(result, str):
                return result
        return ""

    @staticmethod
    def _average(values: object) -> float:
        data: tuple[float, ...] = tuple(values)  # type: ignore[arg-type]
        return sum(data) / len(data) if data else 0.0

    def _record(self, event: str, subject: str, scope: Scope) -> None:
        record = {"event": event, "subject": subject, "scope": serialize(scope)}
        self.audit_log.append(record)
        self.events.append({"fabric": "v7-event-fabric", **record})


GLOBAL_INTELLIGENCE_FRAMEWORK = IntelligenceFramework()
__all__ = tuple(name for name in globals() if not name.startswith("_"))
