"""Explainable advisory decision support over existing TikTok platform data."""

from __future__ import annotations

from datetime import datetime
from time import perf_counter
from typing import Any

from .adapters import (
    DecisionInputProvider,
    LocalReferenceVault,
    MockDecisionInputProvider,
    ReferenceVault,
)
from .metrics import DecisionMetrics
from .models import (
    DASHBOARD_SECTIONS,
    Decision,
    DecisionApproval,
    DecisionConstraint,
    DecisionContext,
    DecisionEvaluation,
    DecisionHistory,
    DecisionRecommendation,
    DecisionScope,
    DecisionStatus,
    EvidenceRecord,
    RiskLevel,
    utcnow,
)

TRANSITIONS: dict[DecisionStatus, frozenset[DecisionStatus]] = {
    DecisionStatus.DRAFT: frozenset(
        {DecisionStatus.ANALYZING, DecisionStatus.ARCHIVED}
    ),
    DecisionStatus.ANALYZING: frozenset(
        {DecisionStatus.PROPOSED, DecisionStatus.REJECTED}
    ),
    DecisionStatus.PROPOSED: frozenset(
        {DecisionStatus.PENDING_REVIEW, DecisionStatus.REJECTED}
    ),
    DecisionStatus.PENDING_REVIEW: frozenset(
        {DecisionStatus.APPROVED, DecisionStatus.REJECTED}
    ),
    DecisionStatus.APPROVED: frozenset({DecisionStatus.ARCHIVED}),
    DecisionStatus.REJECTED: frozenset({DecisionStatus.ARCHIVED}),
    DecisionStatus.ARCHIVED: frozenset({DecisionStatus.DELETED}),
    DecisionStatus.DELETED: frozenset(),
}

FORBIDDEN_ACTIONS = (
    "captcha",
    "bypass",
    "circumvent",
    "anti-detection",
    "spam",
    "mass_action",
    "unrestricted",
)


class TikTokAIIntelligentDecisionCenter:
    """Generates advisory recommendations and approval-gated handoff references."""

    def __init__(
        self,
        inputs: DecisionInputProvider | None = None,
        vault: ReferenceVault | None = None,
    ) -> None:
        self.inputs = inputs or MockDecisionInputProvider()
        if not self.inputs.read_only:
            raise ValueError("Decision inputs must be read-only.")
        self.vault = vault or LocalReferenceVault()
        self.decisions: dict[str, Decision] = {}
        self.contexts: dict[str, DecisionContext] = {}
        self.evaluations: dict[str, DecisionEvaluation] = {}
        self.recommendations: dict[str, DecisionRecommendation] = {}
        self.approvals: dict[str, DecisionApproval] = {}
        self.evidence: dict[str, EvidenceRecord] = {}
        self.history: list[DecisionHistory] = []
        self.metrics = DecisionMetrics()

    @staticmethod
    def _require(scope: DecisionScope, permission: str) -> None:
        required = f"tiktok:decision:{permission}"
        if (
            required not in scope.permissions
            and "tiktok:decision:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {required}")

    @staticmethod
    def _scoped(item: Any, scope: DecisionScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    @staticmethod
    def _safe_text(value: str) -> None:
        secret_markers = ("password=", "secret=", "token=", "cookie=", "session=")
        if any(marker in value.casefold() for marker in secret_markers):
            raise ValueError("Secrets are forbidden in decision logs.")

    def _record(
        self, decision: Decision, scope: DecisionScope, action: str, detail: str = ""
    ) -> None:
        self._safe_text(detail)
        self.history.append(
            DecisionHistory(
                decision.id,
                decision.tenant,
                decision.workspace,
                scope.actor,
                action,
                detail,
            )
        )

    def create(self, decision: Decision, scope: DecisionScope) -> Decision:
        self._require(scope, "write")
        self._scoped(decision, scope)
        decision.validate()
        if decision.id in self.decisions:
            raise ValueError("Decision ID must be unique.")
        self.decisions[decision.id] = decision
        self.metrics.increment("tiktok_decisions_total")
        self._record(decision, scope, "decision.created")
        return decision

    def transition(
        self, decision_id: str, status: DecisionStatus, scope: DecisionScope
    ) -> Decision:
        self._require(scope, "write")
        decision = self.decisions[decision_id]
        self._scoped(decision, scope)
        if status not in TRANSITIONS[decision.status]:
            raise ValueError(
                "Invalid decision transition: "
                f"{decision.status.value} -> {status.value}"
            )
        decision.status = status
        decision.version += 1
        decision.updated_at = utcnow()
        self._record(decision, scope, f"decision.transition.{status.value}")
        return decision

    def analyze(self, decision_id: str, scope: DecisionScope) -> DecisionEvaluation:
        self._require(scope, "analyze")
        started = perf_counter()
        decision = self.decisions[decision_id]
        self._scoped(decision, scope)
        if decision.status is not DecisionStatus.DRAFT:
            raise ValueError("Only draft decisions may be analyzed.")
        self.transition(decision_id, DecisionStatus.ANALYZING, scope)
        values = self.inputs.collect(scope)
        missing = set(self.inputs_required()) - set(values)
        if missing:
            raise ValueError(f"Missing required decision inputs: {sorted(missing)}")
        for value in values.values():
            if value.get("restriction_active") or value.get("challenge_unresolved"):
                raise PermissionError(
                    "Decision analysis stopped by a platform restriction or challenge."
                )
        context = DecisionContext(
            decision.id, decision.tenant, decision.workspace, values
        )
        self.contexts[decision.id] = context
        scores = [
            float(value.get("score", 0.5))
            for value in values.values()
            if value.get("health") != "unavailable"
        ]
        objective = sum(scores) / len(scores) if scores else 0.0
        risk = 1 - float(values["risk_state"].get("score", 0.5))
        capacity = float(values["resource_utilization"].get("score", 0.5))
        resource = min(capacity, float(values["runtime_state"].get("score", 0.5)))
        constraints = [
            DecisionConstraint(
                "minimum_confidence",
                0.6,
                objective,
                objective >= 0.6,
                "Requires sufficient bounded evidence.",
            ),
            DecisionConstraint(
                "maximum_risk",
                0.5,
                risk,
                risk <= 0.5,
                "High-risk proposals require rejection.",
            ),
            DecisionConstraint(
                "minimum_capacity",
                0.4,
                capacity,
                capacity >= 0.4,
                "Existing resources must report bounded capacity.",
            ),
        ]
        confidence = max(0.0, min(1.0, (objective + capacity + resource) / 3))
        references: list[str] = []
        for name, value in values.items():
            reference = self.vault.protect(str(value.get("source", name)), scope)
            references.append(reference)
            record = EvidenceRecord(
                f"evidence-{decision.id}-{name}",
                decision.id,
                decision.tenant,
                decision.workspace,
                name,
                reference,
                f"Read-only {name} snapshot",
            )
            self.evidence[record.id] = record
        evaluation = DecisionEvaluation(
            f"evaluation-{decision.id}",
            decision.id,
            decision.tenant,
            decision.workspace,
            objective,
            risk,
            capacity,
            resource,
            confidence,
            constraints,
            references,
        )
        self.evaluations[evaluation.id] = evaluation
        self.metrics.set("tiktok_decision_confidence", confidence)
        self.metrics.set("tiktok_decision_latency_seconds", perf_counter() - started)
        self._record(decision, scope, "decision.evaluated")
        return evaluation

    @staticmethod
    def inputs_required() -> tuple[str, ...]:
        from .models import DECISION_INPUTS

        return DECISION_INPUTS

    def recommend(
        self,
        decision_id: str,
        scope: DecisionScope,
        *,
        suggested_action: str,
        suggested_schedule: str,
        suggested_resources: list[str],
        suggested_workflow: str,
        suggested_recovery: str,
        expected_outcome: str,
    ) -> DecisionRecommendation:
        self._require(scope, "recommend")
        decision = self.decisions[decision_id]
        self._scoped(decision, scope)
        if decision.status is not DecisionStatus.ANALYZING:
            raise ValueError("Recommendations require an analyzed decision.")
        action_text = " ".join(
            (
                suggested_action,
                suggested_schedule,
                suggested_workflow,
                suggested_recovery,
            )
        ).casefold()
        if any(term in action_text for term in FORBIDDEN_ACTIONS):
            raise ValueError("Unsafe or unrestricted recommendations are forbidden.")
        evaluation = self.evaluations[f"evaluation-{decision.id}"]
        if not all(item.passed for item in evaluation.constraints):
            raise ValueError("Recommendation constraints did not pass.")
        risk_level = (
            RiskLevel.LOW
            if evaluation.risk_score <= 0.25
            else RiskLevel.MEDIUM
            if evaluation.risk_score <= 0.5
            else RiskLevel.HIGH
        )
        recommendation = DecisionRecommendation(
            f"recommendation-{decision.id}",
            decision.id,
            decision.tenant,
            decision.workspace,
            suggested_action,
            suggested_schedule,
            list(suggested_resources),
            suggested_workflow,
            suggested_recovery,
            expected_outcome,
            evaluation.confidence_score,
            risk_level,
        )
        self.recommendations[recommendation.id] = recommendation
        self.metrics.increment("tiktok_decision_recommendations_total")
        self.transition(decision.id, DecisionStatus.PROPOSED, scope)
        self.transition(decision.id, DecisionStatus.PENDING_REVIEW, scope)
        self._record(decision, scope, "recommendation.created", recommendation.id)
        return recommendation

    def review(
        self,
        decision_id: str,
        recommendation_id: str,
        scope: DecisionScope,
        *,
        approved: bool,
        notes: str,
        expires_at: datetime,
    ) -> DecisionApproval:
        self._require(scope, "approve")
        decision = self.decisions[decision_id]
        recommendation = self.recommendations[recommendation_id]
        self._scoped(decision, scope)
        self._scoped(recommendation, scope)
        self._safe_text(notes)
        if decision.status is not DecisionStatus.PENDING_REVIEW:
            raise ValueError("Only pending decisions may be reviewed.")
        if expires_at <= utcnow():
            raise ValueError("Approval expiration must be in the future.")
        if not notes.strip():
            raise ValueError("Approval notes are required.")
        status = DecisionStatus.APPROVED if approved else DecisionStatus.REJECTED
        handoff = (
            self.vault.protect(
                f"execution-proposal:{decision.id}:{recommendation.id}", scope
            )
            if approved
            else ""
        )
        approval = DecisionApproval(
            f"approval-{decision.id}",
            decision.id,
            recommendation.id,
            decision.tenant,
            decision.workspace,
            scope.actor,
            approved,
            notes,
            expires_at,
            handoff,
        )
        self.approvals[approval.id] = approval
        self.transition(decision.id, status, scope)
        self.metrics.increment("tiktok_decision_approvals_total")
        self._record(decision, scope, "decision.reviewed", status.value)
        return approval

    def scoped(self, values: Any, scope: DecisionScope) -> list[Any]:
        self._require(scope, "read")
        return [
            item
            for item in values
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def analytics(self, scope: DecisionScope) -> dict[str, float]:
        decisions = self.scoped(self.decisions.values(), scope)
        recommendations = self.scoped(self.recommendations.values(), scope)
        approvals = self.scoped(self.approvals.values(), scope)
        confidence = (
            sum(item.confidence for item in recommendations) / len(recommendations)
            if recommendations
            else 0.0
        )
        return {
            "decisions_total": float(len(decisions)),
            "recommendations_total": float(len(recommendations)),
            "approvals_total": float(len(approvals)),
            "approved_total": float(sum(item.approved for item in approvals)),
            "average_confidence": confidence,
        }

    def dashboard(self, scope: DecisionScope) -> dict[str, Any]:
        return {
            "title": "TikTok AI Intelligent Decision Center",
            "sections": list(DASHBOARD_SECTIONS),
            "overview": self.analytics(scope),
            "decisions": len(self.scoped(self.decisions.values(), scope)),
            "recommendations": len(self.scoped(self.recommendations.values(), scope)),
            "evidence": len(self.scoped(self.evidence.values(), scope)),
            "approvals": len(self.scoped(self.approvals.values(), scope)),
            "history": len(self.scoped(self.history, scope)),
            "analytics": self.analytics(scope),
        }
