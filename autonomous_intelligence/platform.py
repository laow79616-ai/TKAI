"""Governed Enterprise AI Autonomous Intelligence control plane."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from time import monotonic
from typing import Any

from .metrics import AutonomousIntelligenceMetrics


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IntelligenceStatus(str, Enum):
    DRAFT = "draft"
    LEARNING = "learning"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ApprovalState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    AUTOMATIC = "automatic"


@dataclass(frozen=True, slots=True)
class IntelligenceScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"autonomous_intelligence:read"})

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class IntelligenceProfile:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    capability_level: int
    version: str = "1.0.0"
    status: IntelligenceStatus = IntelligenceStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        return result


@dataclass(slots=True)
class Awareness:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    environment: dict[str, Any]
    context: dict[str, Any]
    resources: dict[str, float]
    policies: tuple[str, ...]
    risks: dict[str, float]
    confidence: float


@dataclass(slots=True)
class Intent:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    mission: str
    objectives: tuple[str, ...]
    priority: int
    constraints: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    approval_state: ApprovalState = ApprovalState.PENDING


@dataclass(slots=True)
class Goal:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    strategic_goals: tuple[str, ...]
    operational_goals: tuple[str, ...]
    short_term_goals: tuple[str, ...]
    long_term_goals: tuple[str, ...]
    success_criteria: dict[str, float]
    progress: float = 0


@dataclass(slots=True)
class ReasoningRecord:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    evidence: tuple[str, ...]
    steps: tuple[str, ...]
    policy_validated: bool
    risk_evaluation: dict[str, float]
    confidence_score: float
    decision_trace_reference: str


@dataclass(slots=True)
class Plan:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    goal_decomposition: tuple[str, ...]
    execution_graph: dict[str, tuple[str, ...]]
    milestones: tuple[str, ...] = ()
    dependencies: dict[str, tuple[str, ...]] = field(default_factory=dict)
    schedule: dict[str, str] = field(default_factory=dict)
    optimization: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Prediction:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    outcome_prediction: dict[str, float]
    risk_prediction: dict[str, float]
    capacity_forecast: dict[str, float]
    trend_forecast: dict[str, float]
    confidence: float


@dataclass(slots=True)
class LearningCycle:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    continuous_learning: tuple[str, ...]
    outcome_evaluation: dict[str, Any]
    feedback_integration: dict[str, Any]
    version_tracking: str
    improvement_recommendations: tuple[str, ...]


@dataclass(slots=True)
class Reflection:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    execution_review: dict[str, Any]
    performance_review: dict[str, float]
    root_cause_analysis: tuple[str, ...]
    lessons_learned: tuple[str, ...]
    self_evaluation: float


@dataclass(slots=True)
class Adaptation:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    policy_adjustment: dict[str, Any]
    strategy_selection: str
    threshold_tuning: dict[str, float]
    resource_adaptation: dict[str, float]
    fallback_strategy: str


@dataclass(slots=True)
class Execution:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    mode: str
    tasks: tuple[str, ...]
    checkpoint: str
    rollback_reference: str
    recovery_strategy: str
    approval_gates: tuple[str, ...] = ()
    completed_tasks: tuple[str, ...] = ()
    state: str = "pending"


@dataclass(slots=True)
class Coordination:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    agents: tuple[str, ...]
    shared_context_reference: str
    task_delegation: dict[str, str]
    consensus_reference: str
    conflict_resolution: str


@dataclass(slots=True)
class MonitoringRecord:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    health: str
    latency: float
    utilization: dict[str, float]
    failures: tuple[str, ...]
    confidence_trend: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class AuditEntry:
    action: str
    actor: str
    tenant: str
    workspace: str
    occurred_at: datetime
    metadata: dict[str, Any]


class AutonomousIntelligencePlatform:
    """Secure in-memory reference control plane for autonomous intelligence."""

    TRANSITIONS = {
        IntelligenceStatus.DRAFT: {
            IntelligenceStatus.LEARNING,
            IntelligenceStatus.ARCHIVED,
        },
        IntelligenceStatus.LEARNING: {
            IntelligenceStatus.READY,
            IntelligenceStatus.PAUSED,
            IntelligenceStatus.ARCHIVED,
        },
        IntelligenceStatus.READY: {
            IntelligenceStatus.RUNNING,
            IntelligenceStatus.LEARNING,
            IntelligenceStatus.ARCHIVED,
        },
        IntelligenceStatus.RUNNING: {
            IntelligenceStatus.PAUSED,
            IntelligenceStatus.COMPLETED,
        },
        IntelligenceStatus.PAUSED: {
            IntelligenceStatus.RUNNING,
            IntelligenceStatus.LEARNING,
            IntelligenceStatus.ARCHIVED,
        },
        IntelligenceStatus.COMPLETED: {IntelligenceStatus.ARCHIVED},
        IntelligenceStatus.ARCHIVED: {IntelligenceStatus.DELETED},
        IntelligenceStatus.DELETED: set(),
    }

    def __init__(self) -> None:
        self.profiles: dict[str, IntelligenceProfile] = {}
        self.awareness_records: list[Awareness] = []
        self.intents: list[Intent] = []
        self.goals: list[Goal] = []
        self.reasoning_records: list[ReasoningRecord] = []
        self.plans: list[Plan] = []
        self.predictions: list[Prediction] = []
        self.learning_cycles: list[LearningCycle] = []
        self.reflections: list[Reflection] = []
        self.adaptations: list[Adaptation] = []
        self.executions: list[Execution] = []
        self.coordination_records: list[Coordination] = []
        self.monitoring_records: list[MonitoringRecord] = []
        self.audit: list[AuditEntry] = []
        self.metrics = AutonomousIntelligenceMetrics()

    @staticmethod
    def _check(record: Any, scope: IntelligenceScope) -> None:
        if record.tenant != scope.tenant or record.workspace != scope.workspace:
            raise PermissionError("Cross-scope autonomous intelligence access denied.")

    @staticmethod
    def _require(scope: IntelligenceScope, permission: str) -> None:
        if (
            permission not in scope.permissions
            and "autonomous_intelligence:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    def _audit(self, action: str, scope: IntelligenceScope, **metadata: Any) -> None:
        safe = {
            key: value
            for key, value in metadata.items()
            if not any(
                term in key.lower()
                for term in ("secret", "token", "password", "credential", "key")
            )
        }
        self.audit.append(
            AuditEntry(
                action, scope.actor, scope.tenant, scope.workspace, utcnow(), safe
            )
        )

    def _profile(
        self, profile_id: str, scope: IntelligenceScope
    ) -> IntelligenceProfile:
        profile = self.profiles[profile_id]
        self._check(profile, scope)
        return profile

    @staticmethod
    def _confidence(value: float) -> None:
        if not 0 <= value <= 1:
            raise ValueError("Confidence must be within [0, 1].")

    @staticmethod
    def _ratios(values: dict[str, float]) -> None:
        if any(not 0 <= value <= 1 for value in values.values()):
            raise ValueError("Risk and threshold values must be within [0, 1].")

    def _record(
        self,
        item: Any,
        scope: IntelligenceScope,
        permission: str,
        records: list[Any],
        action: str,
        validator: Callable[[Any], None] | None = None,
    ) -> Any:
        self._require(scope, permission)
        self._check(item, scope)
        self._profile(item.profile_id, scope)
        if validator:
            validator(item)
        records.append(item)
        self._audit(action, scope, record_id=item.id, profile_id=item.profile_id)
        return item

    def create_profile(
        self, profile: IntelligenceProfile, scope: IntelligenceScope
    ) -> IntelligenceProfile:
        self._require(scope, "autonomous_intelligence:write")
        self._check(profile, scope)
        if profile.id in self.profiles:
            raise ValueError("Profile ID must be unique.")
        if not 1 <= profile.capability_level <= 5:
            raise ValueError("Capability level must be within [1, 5].")
        self.profiles[profile.id] = profile
        self.metrics.increment("autonomous_intelligence_profiles_total")
        self._audit("profile.create", scope, profile_id=profile.id)
        return profile

    def list_profiles(self, scope: IntelligenceScope) -> list[IntelligenceProfile]:
        self._require(scope, "autonomous_intelligence:read")
        return [
            item
            for item in self.profiles.values()
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def set_status(
        self,
        profile_id: str,
        status: IntelligenceStatus,
        scope: IntelligenceScope,
    ) -> IntelligenceProfile:
        self._require(scope, "autonomous_intelligence:write")
        profile = self._profile(profile_id, scope)
        if status not in self.TRANSITIONS[profile.status]:
            raise ValueError(
                f"Invalid transition: {profile.status.value} -> {status.value}"
            )
        profile.status = status
        self._audit("profile.status", scope, profile_id=profile_id, status=status.value)
        return profile

    def observe(self, item: Awareness, scope: IntelligenceScope) -> Awareness:
        def validate(value: Awareness) -> None:
            self._confidence(value.confidence)
            self._ratios(value.risks)
            if not value.environment or not value.context:
                raise ValueError("Awareness requires environment and context.")

        return self._record(
            item,
            scope,
            "autonomous_intelligence:observe",
            self.awareness_records,
            "awareness.observe",
            validate,
        )

    def set_intent(self, item: Intent, scope: IntelligenceScope) -> Intent:
        def validate(value: Intent) -> None:
            if not value.mission or not value.objectives or value.priority < 0:
                raise ValueError("Intent requires mission, objectives, and priority.")
            if value.approval_state is ApprovalState.DENIED:
                raise PermissionError("Denied intent cannot be activated.")

        return self._record(
            item,
            scope,
            "autonomous_intelligence:write",
            self.intents,
            "intent.set",
            validate,
        )

    def define_goal(self, item: Goal, scope: IntelligenceScope) -> Goal:
        def validate(value: Goal) -> None:
            self._confidence(value.progress)
            if not value.success_criteria:
                raise ValueError("Goals require measurable success criteria.")

        return self._record(
            item,
            scope,
            "autonomous_intelligence:write",
            self.goals,
            "goal.define",
            validate,
        )

    def reason(
        self, item: ReasoningRecord, scope: IntelligenceScope
    ) -> ReasoningRecord:
        started = monotonic()

        def validate(value: ReasoningRecord) -> None:
            self._confidence(value.confidence_score)
            self._ratios(value.risk_evaluation)
            if (
                not value.evidence
                or not value.steps
                or not value.policy_validated
                or not value.decision_trace_reference
            ):
                raise PermissionError(
                    "Reasoning requires evidence, policy validation, and a trace."
                )

        result = self._record(
            item,
            scope,
            "autonomous_intelligence:reason",
            self.reasoning_records,
            "reasoning.complete",
            validate,
        )
        self.metrics.increment("autonomous_reasoning_total")
        self.metrics.increment("autonomous_latency_seconds", monotonic() - started)
        return result

    @staticmethod
    def _topological(graph: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
        pending = dict(graph)
        complete: list[str] = []
        while pending:
            ready = sorted(
                key
                for key, dependencies in pending.items()
                if set(dependencies).issubset(complete)
            )
            if not ready:
                raise ValueError("Execution graph contains a cycle or unknown task.")
            for key in ready:
                complete.append(key)
                pending.pop(key)
        return tuple(complete)

    def create_plan(self, item: Plan, scope: IntelligenceScope) -> Plan:
        def validate(value: Plan) -> None:
            tasks = set(value.execution_graph)
            if not tasks or any(
                not set(dependencies).issubset(tasks)
                for dependencies in value.execution_graph.values()
            ):
                raise ValueError("Execution dependencies must reference known tasks.")
            self._topological(value.execution_graph)

        return self._record(
            item,
            scope,
            "autonomous_intelligence:plan",
            self.plans,
            "planning.create",
            validate,
        )

    def predict(self, item: Prediction, scope: IntelligenceScope) -> Prediction:
        def validate(value: Prediction) -> None:
            self._confidence(value.confidence)
            self._ratios(value.outcome_prediction)
            self._ratios(value.risk_prediction)

        result = self._record(
            item,
            scope,
            "autonomous_intelligence:predict",
            self.predictions,
            "prediction.complete",
            validate,
        )
        self.metrics.increment("autonomous_predictions_total")
        return result

    def learn(self, item: LearningCycle, scope: IntelligenceScope) -> LearningCycle:
        def validate(value: LearningCycle) -> None:
            if not value.version_tracking or not value.outcome_evaluation:
                raise ValueError("Learning requires outcome evaluation and versioning.")

        result = self._record(
            item,
            scope,
            "autonomous_intelligence:learn",
            self.learning_cycles,
            "learning.complete",
            validate,
        )
        self.metrics.increment("autonomous_learning_cycles_total")
        return result

    def reflect(self, item: Reflection, scope: IntelligenceScope) -> Reflection:
        def validate(value: Reflection) -> None:
            self._confidence(value.self_evaluation)
            if not value.execution_review:
                raise ValueError("Reflection requires an execution review.")

        return self._record(
            item,
            scope,
            "autonomous_intelligence:reflect",
            self.reflections,
            "reflection.complete",
            validate,
        )

    def adapt(self, item: Adaptation, scope: IntelligenceScope) -> Adaptation:
        def validate(value: Adaptation) -> None:
            self._ratios(value.threshold_tuning)
            if not value.strategy_selection or not value.fallback_strategy:
                raise ValueError("Adaptation requires primary and fallback strategies.")

        result = self._record(
            item,
            scope,
            "autonomous_intelligence:adapt",
            self.adaptations,
            "adaptation.apply",
            validate,
        )
        self.metrics.increment("autonomous_adaptations_total")
        return result

    def execute(self, item: Execution, scope: IntelligenceScope) -> Execution:
        started = monotonic()

        def validate(value: Execution) -> None:
            if value.mode not in {"parallel", "sequential"} or not value.tasks:
                raise ValueError("Execution requires tasks and a supported mode.")
            if value.approval_gates:
                self._require(scope, "autonomous_intelligence:approve")
            if not value.checkpoint or not value.rollback_reference:
                raise ValueError(
                    "Execution requires checkpoint and rollback references."
                )
            value.completed_tasks = value.tasks
            value.state = "completed"

        result = self._record(
            item,
            scope,
            "autonomous_intelligence:execute",
            self.executions,
            "execution.complete",
            validate,
        )
        self.metrics.increment("autonomous_execution_total")
        self.metrics.increment("autonomous_latency_seconds", monotonic() - started)
        return result

    def rollback(self, execution_id: str, scope: IntelligenceScope) -> Execution:
        self._require(scope, "autonomous_intelligence:execute")
        item = next(record for record in self.executions if record.id == execution_id)
        self._check(item, scope)
        item.completed_tasks = ()
        item.state = "rolled_back"
        self._audit("execution.rollback", scope, execution_id=execution_id)
        return item

    def recover(self, execution_id: str, scope: IntelligenceScope) -> Execution:
        self._require(scope, "autonomous_intelligence:execute")
        item = next(record for record in self.executions if record.id == execution_id)
        self._check(item, scope)
        if item.state != "rolled_back":
            raise ValueError("Only rolled-back executions can be recovered.")
        item.completed_tasks = item.tasks
        item.state = "recovered"
        self._audit("execution.recover", scope, execution_id=execution_id)
        return item

    def coordinate(
        self, item: Coordination, scope: IntelligenceScope
    ) -> Coordination:
        def validate(value: Coordination) -> None:
            if (
                not value.agents
                or not value.shared_context_reference
                or not value.consensus_reference
            ):
                raise ValueError(
                    "Coordination requires agents, context, and consensus."
                )
            if not set(value.task_delegation.values()).issubset(value.agents):
                raise ValueError("Tasks may only be delegated to registered agents.")

        return self._record(
            item,
            scope,
            "autonomous_intelligence:coordinate",
            self.coordination_records,
            "coordination.complete",
            validate,
        )

    def monitor(
        self, item: MonitoringRecord, scope: IntelligenceScope
    ) -> MonitoringRecord:
        def validate(value: MonitoringRecord) -> None:
            if value.latency < 0 or any(
                number < 0 for number in value.utilization.values()
            ):
                raise ValueError("Monitoring measurements cannot be negative.")
            for confidence in value.confidence_trend:
                self._confidence(confidence)

        return self._record(
            item,
            scope,
            "autonomous_intelligence:monitor",
            self.monitoring_records,
            "monitoring.record",
            validate,
        )

    def dashboard(self, scope: IntelligenceScope) -> dict[str, Any]:
        self._require(scope, "autonomous_intelligence:read")

        def scoped(items: list[Any]) -> list[dict[str, Any]]:
            return [
                asdict(item)
                for item in items
                if item.tenant == scope.tenant and item.workspace == scope.workspace
            ]

        profiles = self.list_profiles(scope)
        monitoring = scoped(self.monitoring_records)
        return {
            "intelligence": [item.to_dict() for item in profiles],
            "awareness": scoped(self.awareness_records),
            "intent": scoped(self.intents),
            "goals": scoped(self.goals),
            "reasoning": scoped(self.reasoning_records),
            "planning": scoped(self.plans),
            "prediction": scoped(self.predictions),
            "learning": scoped(self.learning_cycles),
            "reflection": scoped(self.reflections),
            "adaptation": scoped(self.adaptations),
            "execution": scoped(self.executions),
            "coordination": scoped(self.coordination_records),
            "monitoring": {
                "health": (
                    "degraded"
                    if any(item["failures"] for item in monitoring)
                    else "healthy"
                ),
                "records": monitoring,
                "audit_events": len(
                    [
                        item
                        for item in self.audit
                        if item.tenant == scope.tenant
                        and item.workspace == scope.workspace
                    ]
                ),
            },
            "metrics": self.metrics.snapshot(),
        }


EnterpriseAIAutonomousIntelligencePlatform = AutonomousIntelligencePlatform
