"""Secure, explainable Enterprise AI Decision Intelligence control plane."""

from __future__ import annotations

import math
import re
import secrets
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol, TypeVar

from .metrics import DecisionMetrics


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DecisionStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Scoped(Protocol):
    id: str
    tenant: str
    workspace: str


ScopedT = TypeVar("ScopedT", bound=Scoped)


@dataclass(frozen=True, slots=True)
class DecisionScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"decision_intelligence:read"})

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class DecisionContext:
    business_context: dict[str, Any] = field(default_factory=dict)
    operational_context: dict[str, Any] = field(default_factory=dict)
    technical_context: dict[str, Any] = field(default_factory=dict)
    risk_context: dict[str, Any] = field(default_factory=dict)
    historical_context: dict[str, Any] = field(default_factory=dict)
    dependencies: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()


@dataclass(slots=True)
class Objective:
    id: str
    name: str
    primary: bool
    weight: float
    kpis: dict[str, float] = field(default_factory=dict)
    success_criteria: tuple[str, ...] = ()
    time_horizon: str = ""
    business_value: float = 0

    def __post_init__(self) -> None:
        if not 0 <= self.weight <= 1:
            raise ValueError("Objective weight must be between zero and one.")


@dataclass(slots=True)
class Alternative:
    id: str
    name: str
    description: str = ""
    trade_offs: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    estimated_cost: float = 0
    estimated_benefit: float = 0
    risk: float = 0
    confidence: float = 1
    attributes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.estimated_cost < 0 or self.estimated_benefit < 0:
            raise ValueError("Cost and benefit cannot be negative.")
        if not 0 <= self.risk <= 1 or not 0 <= self.confidence <= 1:
            raise ValueError("Risk and confidence must be between zero and one.")


@dataclass(slots=True)
class DecisionConstraints:
    budget: float | None = None
    time: str | None = None
    resources: tuple[str, ...] = ()
    compliance: tuple[str, ...] = ()
    security: tuple[str, ...] = ()
    performance: dict[str, float] = field(default_factory=dict)
    custom: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.budget is not None and self.budget < 0:
            raise ValueError("Budget cannot be negative.")


@dataclass(slots=True)
class Decision:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    category: str
    priority: Priority = Priority.MEDIUM
    status: DecisionStatus = DecisionStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)
    context: DecisionContext = field(default_factory=DecisionContext)
    objectives: list[Objective] = field(default_factory=list)
    alternatives: list[Alternative] = field(default_factory=list)
    constraints: DecisionConstraints = field(default_factory=DecisionConstraints)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["priority"] = self.priority.value
        result["status"] = self.status.value
        result["created_at"] = self.created_at.isoformat()
        result["updated_at"] = self.updated_at.isoformat()
        return result


@dataclass(slots=True)
class Evaluation:
    id: str
    decision_id: str
    tenant: str
    workspace: str
    weights: dict[str, float]
    scores: dict[str, dict[str, float]]
    weighted_scores: dict[str, float]
    risk_assessment: dict[str, float]
    cost_benefit: dict[str, float]
    sensitivity: dict[str, Any]
    scenario_comparison: dict[str, Any]
    created_at: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["created_at"] = self.created_at.isoformat()
        return result


@dataclass(slots=True)
class Recommendation:
    id: str
    decision_id: str
    tenant: str
    workspace: str
    ranked_options: tuple[str, ...]
    rationale: str
    confidence_score: float
    expected_outcome: dict[str, Any]
    supporting_evidence_references: tuple[str, ...]
    created_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        if not 0 <= self.confidence_score <= 1:
            raise ValueError("Recommendation confidence must be between zero and one.")

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["created_at"] = self.created_at.isoformat()
        return result


@dataclass(slots=True)
class Approval:
    id: str
    decision_id: str
    tenant: str
    workspace: str
    reviewers: tuple[str, ...]
    status: ApprovalStatus = ApprovalStatus.PENDING
    comments: list[str] = field(default_factory=list)
    decision_log: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        result["created_at"] = self.created_at.isoformat()
        return result


@dataclass(slots=True)
class Explanation:
    id: str
    decision_id: str
    tenant: str
    workspace: str
    decision_summary: str
    reasoning_trace_reference: str
    factors: tuple[str, ...]
    trade_offs: tuple[str, ...]
    evidence_references: tuple[str, ...]


@dataclass(slots=True)
class Simulation:
    id: str
    decision_id: str
    tenant: str
    workspace: str
    scenario: dict[str, float]
    forecast: dict[str, float]
    comparison: dict[str, Any]
    rollback_impact: dict[str, Any]
    optimization_suggestions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Insight:
    id: str
    decision_id: str
    tenant: str
    workspace: str
    trends: tuple[str, ...]
    patterns: tuple[str, ...]
    anomalies: tuple[str, ...]
    decision_quality: float
    execution_success: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AuditEntry:
    action: str
    actor: str
    tenant: str
    workspace: str
    occurred_at: datetime
    metadata: dict[str, Any]


class DecisionIntelligencePlatform:
    """Reference decision control plane with deterministic, explainable scoring."""

    TRANSITIONS = {
        DecisionStatus.DRAFT: {DecisionStatus.PROPOSED, DecisionStatus.ARCHIVED},
        DecisionStatus.PROPOSED: {
            DecisionStatus.UNDER_REVIEW,
            DecisionStatus.ARCHIVED,
        },
        DecisionStatus.UNDER_REVIEW: {
            DecisionStatus.APPROVED,
            DecisionStatus.REJECTED,
        },
        DecisionStatus.APPROVED: {
            DecisionStatus.EXECUTED,
            DecisionStatus.ARCHIVED,
        },
        DecisionStatus.REJECTED: {
            DecisionStatus.PROPOSED,
            DecisionStatus.ARCHIVED,
        },
        DecisionStatus.EXECUTED: {DecisionStatus.ARCHIVED},
        DecisionStatus.ARCHIVED: {DecisionStatus.DELETED},
        DecisionStatus.DELETED: set(),
    }
    SECRET_KEYS = re.compile(
        r"(?:password|passwd|secret|token|api[_-]?key|authorization|credential)",
        re.I,
    )

    def __init__(self) -> None:
        self.decisions: dict[str, Decision] = {}
        self.evaluations: dict[str, Evaluation] = {}
        self.recommendations: dict[str, Recommendation] = {}
        self.approvals: dict[str, Approval] = {}
        self.explanations: dict[str, Explanation] = {}
        self.simulations: dict[str, Simulation] = {}
        self.insights: dict[str, Insight] = {}
        self.audit: list[AuditEntry] = []
        self.metrics = DecisionMetrics()

    @staticmethod
    def _in_scope(record: Scoped, scope: DecisionScope) -> bool:
        return record.tenant == scope.tenant and record.workspace == scope.workspace

    @staticmethod
    def _require(scope: DecisionScope, permission: str) -> None:
        if (
            permission not in scope.permissions
            and "decision_intelligence:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    def _get(
        self, records: dict[str, ScopedT], record_id: str, scope: DecisionScope
    ) -> ScopedT:
        record = records[record_id]
        if not self._in_scope(record, scope):
            raise PermissionError("Cross-tenant or cross-workspace access denied.")
        return record

    def _validate_safe(self, value: Any) -> None:
        if isinstance(value, dict):
            if any(self.SECRET_KEYS.search(str(key)) for key in value):
                raise ValueError("Sensitive data is not allowed in decision records.")
            for nested in value.values():
                self._validate_safe(nested)
        elif isinstance(value, (list, tuple)):
            for nested in value:
                self._validate_safe(nested)

    def _audit(self, action: str, scope: DecisionScope, **metadata: Any) -> None:
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

    def create_decision(
        self, decision: Decision, scope: DecisionScope
    ) -> Decision:
        self._require(scope, "decision_intelligence:write")
        if not self._in_scope(decision, scope):
            raise PermissionError("Cross-tenant or cross-workspace write denied.")
        if decision.id in self.decisions:
            raise ValueError("Decision already exists.")
        self._validate_safe(decision.to_dict())
        self.decisions[decision.id] = decision
        self.metrics.increment("decisions_total")
        self._audit("decision.create", scope, decision_id=decision.id)
        return decision

    def set_status(
        self, decision_id: str, status: DecisionStatus, scope: DecisionScope
    ) -> Decision:
        self._require(scope, "decision_intelligence:write")
        decision = self._get(self.decisions, decision_id, scope)
        if status not in self.TRANSITIONS[decision.status]:
            raise ValueError("Invalid decision lifecycle transition.")
        if status is DecisionStatus.APPROVED:
            approvals = [
                item
                for item in self.approvals.values()
                if item.decision_id == decision_id and self._in_scope(item, scope)
            ]
            if not approvals or any(
                item.status is not ApprovalStatus.APPROVED for item in approvals
            ):
                raise ValueError("Approved decisions require completed approvals.")
        decision.status = status
        decision.updated_at = utcnow()
        if status is DecisionStatus.EXECUTED:
            self.metrics.increment("decision_execution_success_total")
            latency = (decision.updated_at - decision.created_at).total_seconds()
            self.metrics.observe("decision_latency_seconds", latency)
        self._audit(
            "decision.status",
            scope,
            decision_id=decision_id,
            status=status.value,
        )
        return decision

    def evaluate(
        self,
        decision_id: str,
        weights: dict[str, float],
        scores: dict[str, dict[str, float]],
        scope: DecisionScope,
        *,
        scenario_comparison: dict[str, Any] | None = None,
    ) -> Evaluation:
        self._require(scope, "decision_intelligence:evaluate")
        decision = self._get(self.decisions, decision_id, scope)
        if not weights or not math.isclose(sum(weights.values()), 1, abs_tol=1e-6):
            raise ValueError("Evaluation weights must sum to one.")
        alternative_ids = {item.id for item in decision.alternatives}
        if set(scores) != alternative_ids:
            raise ValueError("Scores must cover every candidate alternative.")
        for option_scores in scores.values():
            if set(option_scores) != set(weights):
                raise ValueError("Every alternative must score every criterion.")
            if any(value < 0 or value > 100 for value in option_scores.values()):
                raise ValueError("Criterion scores must be between zero and 100.")
        alternatives = {item.id: item for item in decision.alternatives}
        weighted = {
            option: sum(values[key] * weights[key] for key in weights)
            * alternatives[option].confidence
            for option, values in scores.items()
        }
        risk = {item.id: item.risk for item in decision.alternatives}
        cost_benefit = {
            item.id: item.estimated_benefit - item.estimated_cost
            for item in decision.alternatives
        }
        sensitivity = {
            option: {
                key: values[key] * weight
                for key, weight in weights.items()
            }
            for option, values in scores.items()
        }
        evaluation = Evaluation(
            secrets.token_hex(12),
            decision_id,
            scope.tenant,
            scope.workspace,
            dict(weights),
            {key: dict(value) for key, value in scores.items()},
            weighted,
            risk,
            cost_benefit,
            sensitivity,
            scenario_comparison or {},
        )
        self.evaluations[evaluation.id] = evaluation
        self.metrics.increment("decision_evaluations_total")
        self._audit(
            "evaluation.create",
            scope,
            decision_id=decision_id,
            evaluation_id=evaluation.id,
        )
        return evaluation

    def recommend(
        self,
        decision_id: str,
        evaluation_id: str,
        scope: DecisionScope,
        *,
        evidence_references: tuple[str, ...] = (),
    ) -> Recommendation:
        self._require(scope, "decision_intelligence:recommend")
        decision = self._get(self.decisions, decision_id, scope)
        evaluation = self._get(self.evaluations, evaluation_id, scope)
        if evaluation.decision_id != decision_id:
            raise ValueError("Evaluation belongs to another decision.")
        ranked = tuple(
            sorted(
                evaluation.weighted_scores,
                key=lambda option: (
                    evaluation.weighted_scores[option],
                    -evaluation.risk_assessment[option],
                    evaluation.cost_benefit[option],
                ),
                reverse=True,
            )
        )
        best = ranked[0]
        alternative = next(item for item in decision.alternatives if item.id == best)
        confidence = min(
            1.0,
            max(0.0, evaluation.weighted_scores[best] / 100),
        )
        recommendation = Recommendation(
            secrets.token_hex(12),
            decision_id,
            scope.tenant,
            scope.workspace,
            ranked,
            (
                f"{alternative.name} ranks first by weighted multi-criteria score "
                f"({evaluation.weighted_scores[best]:.2f}), adjusted for confidence."
            ),
            confidence,
            {
                "option": best,
                "net_benefit": evaluation.cost_benefit[best],
                "risk": evaluation.risk_assessment[best],
            },
            evidence_references,
        )
        self.recommendations[recommendation.id] = recommendation
        self.metrics.increment("decision_recommendations_total")
        self._audit(
            "recommendation.create",
            scope,
            decision_id=decision_id,
            recommendation_id=recommendation.id,
        )
        return recommendation

    def request_approval(
        self,
        decision_id: str,
        reviewers: tuple[str, ...],
        scope: DecisionScope,
    ) -> Approval:
        self._require(scope, "decision_intelligence:approve")
        self._get(self.decisions, decision_id, scope)
        if not reviewers:
            raise ValueError("At least one reviewer is required.")
        approval = Approval(
            secrets.token_hex(12),
            decision_id,
            scope.tenant,
            scope.workspace,
            reviewers,
        )
        self.approvals[approval.id] = approval
        self.metrics.increment("decision_approvals_total")
        self._audit(
            "approval.request",
            scope,
            decision_id=decision_id,
            approval_id=approval.id,
        )
        return approval

    def review_approval(
        self,
        approval_id: str,
        status: ApprovalStatus,
        comment: str,
        scope: DecisionScope,
    ) -> Approval:
        self._require(scope, "decision_intelligence:approve")
        approval = self._get(self.approvals, approval_id, scope)
        if scope.actor not in approval.reviewers:
            raise PermissionError("Actor is not an assigned reviewer.")
        if status is ApprovalStatus.PENDING:
            raise ValueError("A review must approve or reject.")
        approval.status = status
        approval.comments.append(comment)
        approval.decision_log.append(
            {
                "reviewer": scope.actor,
                "status": status.value,
                "comment": comment,
                "occurred_at": utcnow().isoformat(),
            }
        )
        self._audit(
            "approval.review",
            scope,
            approval_id=approval_id,
            status=status.value,
        )
        return approval

    def explain(
        self,
        recommendation_id: str,
        reasoning_trace_reference: str,
        scope: DecisionScope,
    ) -> Explanation:
        self._require(scope, "decision_intelligence:read")
        recommendation = self._get(
            self.recommendations, recommendation_id, scope
        )
        decision = self._get(self.decisions, recommendation.decision_id, scope)
        top = recommendation.ranked_options[0]
        option = next(item for item in decision.alternatives if item.id == top)
        explanation = Explanation(
            secrets.token_hex(12),
            decision.id,
            scope.tenant,
            scope.workspace,
            recommendation.rationale,
            reasoning_trace_reference,
            tuple(decision.context.assumptions),
            option.trade_offs,
            recommendation.supporting_evidence_references,
        )
        self.explanations[explanation.id] = explanation
        self._audit(
            "explanation.create",
            scope,
            decision_id=decision.id,
            explanation_id=explanation.id,
        )
        return explanation

    def simulate(
        self,
        decision_id: str,
        scenario: dict[str, float],
        scope: DecisionScope,
        *,
        baseline: dict[str, float] | None = None,
    ) -> Simulation:
        self._require(scope, "decision_intelligence:simulate")
        self._get(self.decisions, decision_id, scope)
        self._validate_safe(scenario)
        current = baseline or {}
        forecast = {
            key: current.get(key, 0) + change for key, change in scenario.items()
        }
        simulation = Simulation(
            secrets.token_hex(12),
            decision_id,
            scope.tenant,
            scope.workspace,
            dict(scenario),
            forecast,
            {
                key: {"baseline": current.get(key), "forecast": value}
                for key, value in forecast.items()
            },
            {"restore": dict(current)},
            ("Review material forecast changes before execution.",),
        )
        self.simulations[simulation.id] = simulation
        self.metrics.increment("decision_simulations_total")
        self._audit(
            "simulation.run",
            scope,
            decision_id=decision_id,
            simulation_id=simulation.id,
        )
        return simulation

    def generate_insight(
        self, decision_id: str, scope: DecisionScope
    ) -> Insight:
        self._require(scope, "decision_intelligence:read")
        decision = self._get(self.decisions, decision_id, scope)
        evaluations = [
            item
            for item in self.evaluations.values()
            if item.decision_id == decision_id and self._in_scope(item, scope)
        ]
        recommendations = [
            item
            for item in self.recommendations.values()
            if item.decision_id == decision_id and self._in_scope(item, scope)
        ]
        quality = min(
            1.0,
            (
                bool(decision.objectives)
                + bool(decision.alternatives)
                + bool(evaluations)
                + bool(recommendations)
            )
            / 4,
        )
        insight = Insight(
            secrets.token_hex(12),
            decision_id,
            scope.tenant,
            scope.workspace,
            ("Evaluation coverage is improving.",) if evaluations else (),
            ("Evidence-backed recommendation available.",) if recommendations else (),
            () if decision.alternatives else ("No alternatives recorded.",),
            quality,
            1.0 if decision.status is DecisionStatus.EXECUTED else None,
        )
        self.insights[insight.id] = insight
        self._audit(
            "insight.generate",
            scope,
            decision_id=decision_id,
            insight_id=insight.id,
        )
        return insight

    def dashboard(self, scope: DecisionScope) -> dict[str, Any]:
        self._require(scope, "decision_intelligence:read")

        def scoped(values: Any) -> list[Any]:
            return [item for item in values if self._in_scope(item, scope)]

        decisions = scoped(self.decisions.values())
        return {
            "decisions": [item.to_dict() for item in decisions],
            "objectives": {
                item.id: [asdict(value) for value in item.objectives]
                for item in decisions
            },
            "alternatives": {
                item.id: [asdict(value) for value in item.alternatives]
                for item in decisions
            },
            "evaluations": [
                item.to_dict() for item in scoped(self.evaluations.values())
            ],
            "recommendations": [
                item.to_dict() for item in scoped(self.recommendations.values())
            ],
            "approvals": [
                item.to_dict() for item in scoped(self.approvals.values())
            ],
            "insights": [item.to_dict() for item in scoped(self.insights.values())],
            "simulations": [
                item.to_dict() for item in scoped(self.simulations.values())
            ],
            "metrics": self.metrics.snapshot(),
        }


EnterpriseAIDecisionIntelligencePlatform = DecisionIntelligencePlatform
