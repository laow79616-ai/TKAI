"""Explainable, bounded and approval-gated TikTok strategy proposals."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from time import perf_counter
from typing import Any

from .adapters import (
    HANDOFF_MODULES,
    INPUT_MODULES,
    NullStrategyHandoffPort,
    NullStrategyInputPort,
    StrategyHandoffPort,
    StrategyInputPort,
)
from .metrics import StrategyMetrics
from .models import (
    ApprovalDecision,
    ApprovalType,
    OptionType,
    RiskLevel,
    Strategy,
    StrategyApproval,
    StrategyContext,
    StrategyEvaluation,
    StrategyHandoff,
    StrategyHistory,
    StrategyOption,
    StrategyRecommendation,
    StrategyReview,
    StrategyScenario,
    StrategyScope,
    StrategyStatus,
    StrategyType,
    utcnow,
    validate_safe_mapping,
)

TRANSITIONS: dict[StrategyStatus, frozenset[StrategyStatus]] = {
    StrategyStatus.DRAFT: frozenset(
        {StrategyStatus.ANALYZING, StrategyStatus.ARCHIVED}
    ),
    StrategyStatus.ANALYZING: frozenset(
        {StrategyStatus.PROPOSED, StrategyStatus.REJECTED}
    ),
    StrategyStatus.PROPOSED: frozenset(
        {StrategyStatus.PENDING_REVIEW, StrategyStatus.DRAFT}
    ),
    StrategyStatus.PENDING_REVIEW: frozenset(
        {StrategyStatus.APPROVED, StrategyStatus.REJECTED}
    ),
    StrategyStatus.APPROVED: frozenset(
        {StrategyStatus.ACTIVE_REFERENCE, StrategyStatus.ARCHIVED}
    ),
    StrategyStatus.REJECTED: frozenset({StrategyStatus.DRAFT, StrategyStatus.ARCHIVED}),
    StrategyStatus.ACTIVE_REFERENCE: frozenset(
        {StrategyStatus.COMPLETED, StrategyStatus.ARCHIVED}
    ),
    StrategyStatus.COMPLETED: frozenset({StrategyStatus.ARCHIVED}),
    StrategyStatus.ARCHIVED: frozenset({StrategyStatus.DRAFT, StrategyStatus.DELETED}),
    StrategyStatus.DELETED: frozenset(),
}

FORBIDDEN_TERMS = (
    "captcha bypass",
    "restriction bypass",
    "security bypass",
    "circumvent",
    "anti-detection",
    "antidetection",
    "spam",
    "mass action",
    "mass_action",
    "bulk messaging",
    "engagement manipulation",
    "unrestricted autonomous",
)

DASHBOARD_SECTIONS = (
    "Strategy Overview",
    "Strategies",
    "Objectives",
    "Contexts",
    "Constraints",
    "Options",
    "Evaluations",
    "Scenarios",
    "Recommendations",
    "Approvals",
    "Handoffs",
    "Reviews",
    "History",
    "Analytics",
)


class TikTokAutonomousStrategyCenter:
    """Produces advisory proposals; it never executes or publishes."""

    def __init__(
        self,
        inputs: dict[str, StrategyInputPort] | None = None,
        handoffs: dict[str, StrategyHandoffPort] | None = None,
    ) -> None:
        supplied_inputs = inputs or {}
        for name, port in supplied_inputs.items():
            if name not in INPUT_MODULES:
                raise ValueError(f"Unsupported strategy input: {name}")
            if not port.read_only:
                raise ValueError("Strategy inputs must be read-only.")
        null_input = NullStrategyInputPort()
        null_handoff = NullStrategyHandoffPort()
        self.inputs = {
            name: supplied_inputs.get(name, null_input) for name in INPUT_MODULES
        }
        self.handoff_ports = {
            name: (handoffs or {}).get(name, null_handoff) for name in HANDOFF_MODULES
        }
        self.strategies: dict[str, Strategy] = {}
        self.contexts: dict[str, StrategyContext] = {}
        self.options: dict[str, StrategyOption] = {}
        self.evaluations: dict[str, StrategyEvaluation] = {}
        self.scenarios: dict[str, StrategyScenario] = {}
        self.recommendations: dict[str, StrategyRecommendation] = {}
        self.approvals: dict[str, StrategyApproval] = {}
        self.handoffs: dict[str, StrategyHandoff] = {}
        self.reviews: dict[str, StrategyReview] = {}
        self.history: list[StrategyHistory] = []
        self.metrics = StrategyMetrics()
        self.kill_switches: set[tuple[str, str]] = set()
        self.workspace_pauses: set[tuple[str, str]] = set()
        self.account_pauses: set[tuple[str, str, str]] = set()

    @staticmethod
    def _require(scope: StrategyScope, action: str) -> None:
        required = f"tiktok:strategy-center:{action}"
        if required not in scope.permissions and (
            "tiktok:strategy-center:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {required}")

    @staticmethod
    def _scoped(item: Any, scope: StrategyScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    @staticmethod
    def _safe_text(*values: str) -> None:
        text = " ".join(values).casefold()
        secret_markers = ("password=", "secret=", "token=", "cookie=", "session=")
        if any(marker in text for marker in secret_markers):
            raise ValueError("Secrets are forbidden in strategy audit records.")
        if any(term in text for term in FORBIDDEN_TERMS):
            raise ValueError("Unsafe or unrestricted strategies are forbidden.")

    def _record(
        self, strategy: Strategy, scope: StrategyScope, action: str, detail: str = ""
    ) -> None:
        self._safe_text(detail)
        self.history.append(
            StrategyHistory(
                strategy.id,
                strategy.tenant,
                strategy.workspace,
                strategy.version,
                strategy.status,
                scope.actor,
                action,
                detail,
            )
        )

    def scoped_values(self, values: Iterable[Any], scope: StrategyScope) -> list[Any]:
        self._require(scope, "read")
        return [
            item
            for item in values
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def create_strategy(self, strategy: Strategy, scope: StrategyScope) -> Strategy:
        self._require(scope, "write")
        self._scoped(strategy, scope)
        self._safe_text(strategy.name, strategy.description)
        strategy.validate()
        if strategy.id in self.strategies:
            raise ValueError("Strategy ID must be unique.")
        self.strategies[strategy.id] = strategy
        self.metrics.increment("tiktok_strategies_total")
        self._record(strategy, scope, "strategy.created")
        return strategy

    create = create_strategy

    def get_strategy(self, strategy_id: str, scope: StrategyScope) -> Strategy:
        self._require(scope, "read")
        strategy = self.strategies[strategy_id]
        self._scoped(strategy, scope)
        return strategy

    def update_strategy(
        self, strategy_id: str, changes: dict[str, Any], scope: StrategyScope
    ) -> Strategy:
        self._require(scope, "write")
        strategy = self.strategies[strategy_id]
        self._scoped(strategy, scope)
        if strategy.status is not StrategyStatus.DRAFT:
            raise ValueError("Only draft strategies may be edited.")
        validate_safe_mapping(changes)
        allowed = {
            "name",
            "description",
            "strategy_type",
            "planning_horizon",
            "priority",
            "objectives",
            "constraints",
            "window_start",
            "window_end",
            "metadata",
        }
        if set(changes) - allowed:
            raise ValueError("Unsupported strategy field.")
        for key, value in changes.items():
            setattr(strategy, key, value)
        strategy.version += 1
        strategy.updated_at = utcnow()
        strategy.validate()
        self._record(strategy, scope, "strategy.updated")
        return strategy

    def transition(
        self, strategy_id: str, status: StrategyStatus, scope: StrategyScope
    ) -> Strategy:
        self._require(scope, "write")
        strategy = self.strategies[strategy_id]
        self._scoped(strategy, scope)
        if status not in TRANSITIONS[strategy.status]:
            current = strategy.status.value
            message = f"Invalid strategy transition: {current} -> {status.value}"
            raise ValueError(message)
        if status is StrategyStatus.APPROVED:
            self._valid_approval(strategy_id, ApprovalType.STRATEGY, scope)
        strategy.status = status
        strategy.version += 1
        strategy.updated_at = utcnow()
        metric = {
            StrategyStatus.PROPOSED: "tiktok_strategies_proposed_total",
            StrategyStatus.APPROVED: "tiktok_strategies_approved_total",
            StrategyStatus.REJECTED: "tiktok_strategies_rejected_total",
        }.get(status)
        if metric:
            self.metrics.increment(metric)
        self._record(strategy, scope, f"strategy.transition.{status.value}")
        return strategy

    def collect_context(
        self, strategy_id: str, scope: StrategyScope
    ) -> StrategyContext:
        self._require(scope, "analyze")
        strategy = self.strategies[strategy_id]
        self._scoped(strategy, scope)
        snapshots: dict[str, dict[str, Any]] = {}
        evidence: list[str] = []
        for name, port in self.inputs.items():
            if not port.read_only:
                raise ValueError("Strategy inputs must remain read-only.")
            value = dict(port.snapshot(scope))
            validate_safe_mapping(value)
            if any(
                value.get(flag)
                for flag in (
                    "restriction_active",
                    "challenge_unresolved",
                    "kill_switch_active",
                    "workspace_paused",
                    "account_paused",
                )
            ):
                raise PermissionError(
                    f"Strategy analysis stopped by {name} safety state."
                )
            snapshots[name] = value
            evidence.append(f"evidence://{scope.tenant}/{scope.workspace}/{name}")
        context = StrategyContext(
            f"context-{strategy.id}",
            strategy.id,
            strategy.tenant,
            strategy.workspace,
            snapshots,
            evidence,
        )
        self.contexts[context.id] = context
        self._record(strategy, scope, "context.captured", context.id)
        return context

    @staticmethod
    def _score(values: Iterable[dict[str, Any]], key: str, default: float) -> float:
        scores = [float(item.get(key, default)) for item in values]
        return max(0.0, min(1.0, sum(scores) / len(scores))) if scores else default

    def analyze(self, strategy_id: str, scope: StrategyScope) -> StrategyRecommendation:
        self._require(scope, "analyze")
        started = perf_counter()
        strategy = self.strategies[strategy_id]
        self._scoped(strategy, scope)
        if strategy.status is StrategyStatus.DRAFT:
            self.transition(strategy.id, StrategyStatus.ANALYZING, scope)
        if strategy.status is not StrategyStatus.ANALYZING:
            raise ValueError("Strategy must be analyzing.")
        try:
            context = self.collect_context(strategy.id, scope)
            values = list(context.inputs.values())
            health = self._score(values, "health", 0.5)
            capacity = self._score(values, "capacity", 0.5)
            risk = self._score(values, "risk", 0.25)
            historical = self._score(values, "historical_score", health)
            requested = max(
                (constraint.requested for constraint in strategy.constraints),
                default=1.0,
            )
            maximum = max(
                (constraint.maximum for constraint in strategy.constraints),
                default=requested,
            )
            allocation = min(requested, maximum, max(1.0, capacity * maximum))
            option_kinds = [
                OptionType.CONSERVATIVE,
                OptionType.BALANCED,
                OptionType.RELIABILITY_FOCUSED,
                OptionType.RISK_REDUCTION,
                OptionType.MANUAL_ASSISTED,
            ]
            if risk <= 0.25 and health >= 0.7:
                option_kinds.append(OptionType.PERFORMANCE_FOCUSED)
                if strategy.strategy_type is StrategyType.GROWTH:
                    option_kinds.append(OptionType.GROWTH_FOCUSED)
            for index, kind in enumerate(option_kinds, start=1):
                option = StrategyOption(
                    f"option-{strategy.id}-{index}",
                    strategy.id,
                    strategy.tenant,
                    strategy.workspace,
                    kind,
                    [strategy.planning_horizon.value],
                    {"bounded_capacity": allocation},
                    [objective.kind.value for objective in strategy.objectives],
                    ["pause", "review", "reference last known-good plan"],
                    "Bounded objectives improve within approved limits.",
                )
                self.options[option.id] = option
                objective_score = (health + historical) / 2
                compliance = float(
                    all(
                        item.minimum <= item.requested <= item.maximum
                        for item in strategy.constraints
                    )
                )
                feasibility = min(health, capacity)
                confidence = max(
                    0.0,
                    min(
                        0.99,
                        (
                            objective_score
                            + compliance
                            + (1 - risk)
                            + capacity
                            + feasibility
                            + historical
                        )
                        / 6,
                    ),
                )
                evaluation = StrategyEvaluation(
                    f"evaluation-{option.id}",
                    strategy.id,
                    option.id,
                    strategy.tenant,
                    strategy.workspace,
                    objective_score,
                    compliance,
                    risk,
                    capacity,
                    capacity,
                    feasibility,
                    historical,
                    confidence,
                    list(context.evidence_references),
                )
                self.evaluations[evaluation.id] = evaluation
            best = max(
                (
                    item
                    for item in self.evaluations.values()
                    if item.strategy_id == strategy.id
                ),
                key=lambda item: (item.constraint_compliance, item.confidence_score),
            )
            best_option = self.options[best.option_id]
            risk_level = (
                RiskLevel.LOW
                if best.risk_score <= 0.25
                else RiskLevel.MEDIUM
                if best.risk_score <= 0.5
                else RiskLevel.HIGH
                if best.risk_score <= 0.75
                else RiskLevel.CRITICAL
            )
            recommendation = StrategyRecommendation(
                f"recommendation-{strategy.id}",
                strategy.id,
                best_option.id,
                strategy.tenant,
                strategy.workspace,
                [item.kind.value for item in strategy.objectives],
                list(best_option.schedule),
                dict(best_option.resource_allocation),
                list(best_option.mission_types),
                [item.name for item in strategy.constraints],
                list(best_option.recovery_plan),
                best_option.expected_outcome,
                risk_level,
                best.confidence_score,
                list(best.evidence_references),
            )
            self.recommendations[recommendation.id] = recommendation
            self.metrics.increment("tiktok_strategy_recommendations_total")
            self.metrics.set("tiktok_strategy_confidence", recommendation.confidence)
            self.transition(strategy.id, StrategyStatus.PROPOSED, scope)
            self._record(strategy, scope, "recommendation.created", recommendation.id)
            return recommendation
        except Exception:
            if strategy.status is StrategyStatus.ANALYZING:
                self.transition(strategy.id, StrategyStatus.REJECTED, scope)
            raise
        finally:
            self.metrics.set(
                "tiktok_strategy_analysis_seconds", perf_counter() - started
            )

    def simulate(
        self, scenario: StrategyScenario, scope: StrategyScope
    ) -> StrategyScenario:
        self._require(scope, "simulate")
        self._scoped(scenario, scope)
        strategy = self.strategies[scenario.strategy_id]
        self._scoped(strategy, scope)
        if scenario.live_tiktok_access:
            raise ValueError("Strategy scenarios cannot use live TikTok access.")
        validate_safe_mapping(scenario.assumptions)
        scenario.result = {
            **scenario.result,
            "dry_run": True,
            "bounded": True,
            "advisory": True,
            "strategy_type": strategy.strategy_type.value,
        }
        self.scenarios[scenario.id] = scenario
        self.metrics.increment("tiktok_strategy_scenarios_total")
        self._record(strategy, scope, f"scenario.{scenario.kind.value}", scenario.id)
        return scenario

    def decide(
        self, approval: StrategyApproval, scope: StrategyScope
    ) -> StrategyApproval:
        started = perf_counter()
        self._require(scope, "approve")
        self._scoped(approval, scope)
        strategy = self.strategies[approval.strategy_id]
        self._scoped(strategy, scope)
        if strategy.status not in {
            StrategyStatus.PROPOSED,
            StrategyStatus.PENDING_REVIEW,
        }:
            raise ValueError("Only proposed strategies may be reviewed.")
        if approval.expires_at <= utcnow():
            raise ValueError("Approval expiration must be in the future.")
        self._safe_text(approval.notes, approval.rejection_reason)
        if approval.decision is ApprovalDecision.REJECTED and (
            not approval.rejection_reason.strip()
        ):
            raise ValueError("Rejected strategies require a rejection reason.")
        if strategy.status is StrategyStatus.PROPOSED:
            self.transition(strategy.id, StrategyStatus.PENDING_REVIEW, scope)
        self.approvals[approval.id] = approval
        target = (
            StrategyStatus.APPROVED
            if approval.decision is ApprovalDecision.APPROVED
            else StrategyStatus.REJECTED
        )
        self.transition(strategy.id, target, scope)
        self.metrics.set("tiktok_strategy_approval_seconds", perf_counter() - started)
        self._record(
            strategy, scope, f"approval.{approval.decision.value}", approval.id
        )
        return approval

    def _valid_approval(
        self, strategy_id: str, kind: ApprovalType, scope: StrategyScope
    ) -> StrategyApproval:
        matches = [
            item
            for item in self.approvals.values()
            if item.strategy_id == strategy_id
            and item.kind is kind
            and item.decision is ApprovalDecision.APPROVED
            and item.tenant == scope.tenant
            and item.workspace == scope.workspace
            and item.expires_at > utcnow()
        ]
        if not matches:
            raise PermissionError(f"Valid {kind.value} required.")
        return matches[-1]

    def handoff(
        self, handoff: StrategyHandoff, scope: StrategyScope
    ) -> StrategyHandoff:
        self._require(scope, "handoff")
        self._scoped(handoff, scope)
        strategy = self.strategies[handoff.strategy_id]
        self._scoped(strategy, scope)
        if strategy.status not in {
            StrategyStatus.APPROVED,
            StrategyStatus.ACTIVE_REFERENCE,
        }:
            raise PermissionError("Approved strategy required for handoff.")
        approval = self._valid_approval(strategy.id, ApprovalType.STRATEGY, scope)
        if handoff.approval_reference != approval.id:
            raise PermissionError("Handoff approval reference is invalid.")
        if handoff.recommendation_reference not in self.recommendations:
            raise ValueError("Recommendation reference is invalid.")
        key = (scope.tenant, scope.workspace)
        if key in self.kill_switches or key in self.workspace_pauses:
            raise PermissionError("Kill switch or workspace pause is active.")
        if not handoff.reference_only:
            raise ValueError("Strategy handoffs must be reference-only.")
        target = handoff.target.value
        handoff.accepted_reference = self.handoff_ports[target].accept_reference(
            handoff, scope
        )
        if not handoff.accepted_reference:
            raise ValueError("Handoff adapter must return a reference.")
        self.handoffs[handoff.id] = handoff
        self.metrics.increment("tiktok_strategy_handoffs_total")
        if strategy.status is StrategyStatus.APPROVED:
            self.transition(strategy.id, StrategyStatus.ACTIVE_REFERENCE, scope)
        self._record(strategy, scope, "handoff.reference_only", handoff.id)
        return handoff

    def add_review(
        self, review: StrategyReview, scope: StrategyScope
    ) -> StrategyReview:
        self._require(scope, "review")
        self._scoped(review, scope)
        strategy = self.strategies[review.strategy_id]
        self._scoped(strategy, scope)
        self._safe_text(
            review.summary, *review.lessons_learned, *review.improvement_recommendations
        )
        self.reviews[review.id] = review
        self._record(strategy, scope, f"review.{review.kind.value}", review.id)
        return review

    def analytics(self, scope: StrategyScope) -> dict[str, Any]:
        strategies = self.scoped_values(self.strategies.values(), scope)
        scenarios = self.scoped_values(self.scenarios.values(), scope)
        recommendations = self.scoped_values(self.recommendations.values(), scope)
        approvals = self.scoped_values(self.approvals.values(), scope)
        handoffs = self.scoped_values(self.handoffs.values(), scope)
        confidence = [item.confidence for item in recommendations]
        type_distribution = {
            kind.value: sum(item.strategy_type is kind for item in strategies)
            for kind in StrategyType
        }
        return {
            "strategies_total": len(strategies),
            "strategies_proposed": sum(
                item.status is StrategyStatus.PROPOSED for item in strategies
            ),
            "strategies_approved": sum(
                item.status
                in {
                    StrategyStatus.APPROVED,
                    StrategyStatus.ACTIVE_REFERENCE,
                    StrategyStatus.COMPLETED,
                }
                for item in strategies
            ),
            "strategies_rejected": sum(
                item.status is StrategyStatus.REJECTED for item in strategies
            ),
            "strategies_handed_off": len(handoffs),
            "scenario_count": len(scenarios),
            "average_analysis_time": self.metrics.values[
                "tiktok_strategy_analysis_seconds"
            ],
            "average_approval_time": self.metrics.values[
                "tiktok_strategy_approval_seconds"
            ],
            "confidence_distribution": confidence,
            "average_confidence": (
                sum(confidence) / len(confidence) if confidence else 0.0
            ),
            "strategy_type_distribution": type_distribution,
            "approvals_total": len(approvals),
            "expected_benefit_reference": "recommendation.expected_outcome",
            "observed_outcome_reference": "review.outcome",
        }

    def dashboard(self, scope: StrategyScope) -> dict[str, Any]:
        return {
            "title": "TikTok Autonomous Strategy Center",
            "advisory_only": True,
            "sections": list(DASHBOARD_SECTIONS),
            "strategies": [
                item.to_dict()
                for item in self.scoped_values(self.strategies.values(), scope)
            ],
            "recommendations": [
                asdict(item)
                for item in self.scoped_values(self.recommendations.values(), scope)
            ],
            "analytics": self.analytics(scope),
        }
