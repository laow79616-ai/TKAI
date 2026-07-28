"""Enterprise AI Reasoning Engine facade."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from time import monotonic
from typing import Any
from uuid import uuid4

from .decision import DecisionEngine
from .metrics import ReasoningMetrics
from .models import (
    Decision,
    ExecutionPlan,
    LifecycleState,
    OptimizationResult,
    ReasoningMode,
    ReasoningScope,
    ReasoningSession,
    SimulationResult,
    ValidationResult,
)
from .optimization import Optimizer
from .planner import Planner
from .security import ExecutionLimits, ReasoningSecurity
from .simulation import Simulator
from .validator import ReasoningValidator

TERMINAL_STATES = {
    LifecycleState.COMPLETED,
    LifecycleState.FAILED,
    LifecycleState.CANCELLED,
    LifecycleState.ARCHIVED,
}

TRANSITIONS = {
    LifecycleState.CREATED: {LifecycleState.PREPARED, LifecycleState.CANCELLED},
    LifecycleState.PREPARED: {LifecycleState.RUNNING, LifecycleState.CANCELLED},
    LifecycleState.RUNNING: {
        LifecycleState.VALIDATED,
        LifecycleState.FAILED,
        LifecycleState.CANCELLED,
    },
    LifecycleState.VALIDATED: {
        LifecycleState.COMPLETED,
        LifecycleState.FAILED,
    },
    LifecycleState.COMPLETED: {LifecycleState.ARCHIVED},
    LifecycleState.FAILED: {LifecycleState.ARCHIVED},
    LifecycleState.CANCELLED: {LifecycleState.ARCHIVED},
    LifecycleState.ARCHIVED: set(),
}


class EnterpriseAIReasoningEngine:
    def __init__(self, *, limits: ExecutionLimits | None = None) -> None:
        self.metrics = ReasoningMetrics()
        self.security = ReasoningSecurity(limits)
        self.planner = Planner()
        self.decision_engine = DecisionEngine()
        self.validator = ReasoningValidator()
        self.simulator = Simulator()
        self.optimizer = Optimizer()
        self._sessions: dict[str, ReasoningSession] = {}
        self._plans: dict[str, ExecutionPlan] = {}
        self._decisions: dict[str, Decision] = {}
        self._validations: dict[str, ValidationResult] = {}
        self._simulations: dict[str, tuple[SimulationResult, ...]] = {}
        self._optimizations: dict[str, OptimizationResult] = {}
        self._started: dict[str, float] = {}

    def create_session(
        self, payload: dict[str, Any], scope: ReasoningScope
    ) -> ReasoningSession:
        self.security.require(scope, "reasoning:write")
        priority = int(payload.get("priority", 50))
        if not 0 <= priority <= 100:
            raise ValueError("Priority must be between zero and 100.")
        session = ReasoningSession(
            id=str(payload.get("id") or uuid4()),
            tenant=scope.tenant,
            workspace=scope.workspace,
            agent=str(payload["agent"]),
            goal=str(payload["goal"]),
            strategy=str(payload.get("strategy", "balanced")),
            mode=ReasoningMode(str(payload.get("mode", "planning"))),
            priority=priority,
            metadata=dict(payload.get("metadata", {})),
        )
        self._sessions[session.id] = session
        self.metrics.increment("reasoning_sessions_total")
        self.security.record(scope, "reasoning:created", session_id=session.id)
        return session

    def get(self, session_id: str, scope: ReasoningScope) -> ReasoningSession:
        self.security.require(scope, "reasoning:read")
        session = self._sessions[session_id]
        self.security.isolate(scope, session)
        return session

    def list(self, scope: ReasoningScope) -> tuple[ReasoningSession, ...]:
        self.security.require(scope, "reasoning:read")
        return tuple(
            session
            for session in self._sessions.values()
            if session.tenant == scope.tenant and session.workspace == scope.workspace
        )

    def transition(
        self,
        session_id: str,
        state: LifecycleState | str,
        scope: ReasoningScope,
    ) -> ReasoningSession:
        self.security.require(scope, "reasoning:execute")
        session = self.get_with_isolation(session_id, scope)
        target = state if isinstance(state, LifecycleState) else LifecycleState(state)
        if target not in TRANSITIONS[session.state]:
            raise ValueError(
                f"Invalid transition: {session.state.value} -> {target.value}."
            )
        session.state = target
        session.updated_at = datetime.now(timezone.utc)
        if target is LifecycleState.RUNNING:
            self._started[session.id] = monotonic()
        if target in TERMINAL_STATES and session.id in self._started:
            self.metrics.increment(
                "reasoning_duration_seconds",
                monotonic() - self._started.pop(session.id),
            )
        self.security.record(
            scope, "reasoning:transitioned", session_id=session.id, state=target.value
        )
        return session

    def create_plan(
        self,
        session_id: str,
        subtasks: Sequence[dict[str, Any]],
        scope: ReasoningScope,
    ) -> ExecutionPlan:
        self.security.require(scope, "reasoning:plan")
        session = self.get_with_isolation(session_id, scope)
        self.security.enforce_plan(len(subtasks))
        plan = self.planner.create(session.goal, list(subtasks))
        self._plans[session.id] = plan
        self.metrics.increment("reasoning_plans_total")
        self.security.record(scope, "reasoning:planned", session_id=session.id)
        return plan

    def decide(
        self,
        session_id: str,
        options: Sequence[dict[str, Any]],
        scope: ReasoningScope,
        **settings: Any,
    ) -> Decision:
        self.security.require(scope, "reasoning:decide")
        session = self.get_with_isolation(session_id, scope)
        decision = self.decision_engine.decide(
            list(options),
            threshold=float(settings.get("threshold", 0.5)),
            fallback=settings.get("fallback"),
            rules=tuple(str(item) for item in settings.get("rules", ())),
        )
        self._decisions[session.id] = decision
        self.metrics.increment("reasoning_decisions_total")
        self.security.record(scope, "reasoning:decided", session_id=session.id)
        return decision

    def validate(
        self,
        session_id: str,
        constraints: dict[str, Any],
        scope: ReasoningScope,
    ) -> ValidationResult:
        self.security.require(scope, "reasoning:validate")
        session = self.get_with_isolation(session_id, scope)
        plan = self._plans[session.id]
        result = self.validator.validate(plan, constraints)
        self._validations[session.id] = result
        if not result.valid:
            self.metrics.increment(
                "reasoning_validation_failures_total", len(result.failures)
            )
        self.security.record(
            scope,
            "reasoning:validated",
            session_id=session.id,
            valid=result.valid,
        )
        return result

    def simulate(
        self,
        session_id: str,
        scenarios: Sequence[dict[str, Any]],
        scope: ReasoningScope,
    ) -> tuple[SimulationResult, ...]:
        self.security.require(scope, "reasoning:simulate")
        session = self.get_with_isolation(session_id, scope)
        self.security.enforce_simulations(len(scenarios))
        results = tuple(
            self.simulator.run(
                str(item["scenario"]),
                {
                    str(key): float(value)
                    for key, value in item.get("variables", {}).items()
                },
                {
                    str(key): float(value)
                    for key, value in item.get("baselines", {}).items()
                },
                tuple(str(value) for value in item.get("rollback_plan", ())),
            )
            for item in scenarios
        )
        self._simulations[session.id] = results
        self.metrics.increment("reasoning_simulations_total", len(results))
        self.security.record(
            scope, "reasoning:simulated", session_id=session.id, count=len(results)
        )
        return results

    def optimize(
        self,
        session_id: str,
        resources: dict[str, float],
        scope: ReasoningScope,
        **settings: Any,
    ) -> OptimizationResult:
        self.security.require(scope, "reasoning:optimize")
        session = self.get_with_isolation(session_id, scope)
        result = self.optimizer.optimize(
            self._plans[session.id],
            resources,
            cost_per_unit=float(settings.get("cost_per_unit", 1)),
            latency_per_task=float(settings.get("latency_per_task", 1)),
        )
        self._optimizations[session.id] = result
        self.security.record(scope, "reasoning:optimized", session_id=session.id)
        return result

    def explain(self, session_id: str, scope: ReasoningScope) -> dict[str, Any]:
        session = self.get(session_id, scope)
        return {
            "session": session.to_dict(),
            "plan": self._serialize(self._plans.get(session.id)),
            "decision": self._serialize(self._decisions.get(session.id)),
            "validation": self._serialize(self._validations.get(session.id)),
            "simulations": [
                item.to_dict() for item in self._simulations.get(session.id, ())
            ],
            "optimization": self._serialize(self._optimizations.get(session.id)),
        }

    def dashboard(self, scope: ReasoningScope) -> dict[str, Any]:
        sessions = self.list(scope)
        identifiers = {session.id for session in sessions}
        return {
            "sections": (
                "Reasoning Sessions",
                "Plans",
                "Decisions",
                "Strategies",
                "Validation",
                "Metrics",
            ),
            "reasoning_sessions": [session.to_dict() for session in sessions],
            "plans": sum(identifier in self._plans for identifier in identifiers),
            "decisions": sum(
                identifier in self._decisions for identifier in identifiers
            ),
            "strategies": sorted({session.strategy for session in sessions}),
            "validation": {
                "total": sum(
                    identifier in self._validations for identifier in identifiers
                ),
                "failures": self.metrics.snapshot()[
                    "reasoning_validation_failures_total"
                ],
            },
            "metrics": self.metrics.snapshot(),
        }

    def get_with_isolation(
        self, session_id: str, scope: ReasoningScope
    ) -> ReasoningSession:
        session = self._sessions[session_id]
        self.security.isolate(scope, session)
        return session

    @staticmethod
    def _serialize(value: Any) -> dict[str, Any] | None:
        return value.to_dict() if value is not None else None
