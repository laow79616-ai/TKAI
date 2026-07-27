"""Governed Enterprise AI Cognitive Architecture control plane."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from time import monotonic
from typing import Any

from .metrics import CognitiveMetrics


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CognitiveStatus(str, Enum):
    DRAFT = "draft"
    TRAINING = "training"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ReasoningMode(str, Enum):
    DEDUCTIVE = "deductive"
    INDUCTIVE = "inductive"
    ABDUCTIVE = "abductive"
    PROBABILISTIC = "probabilistic"
    CONSTRAINT_BASED = "constraint_based"


@dataclass(frozen=True, slots=True)
class CognitiveScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"cognitive:read"})

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class CognitiveModel:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    architecture: dict[str, Any]
    version: str = "1.0.0"
    status: CognitiveStatus = CognitiveStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        return result


@dataclass(slots=True)
class Perception:
    id: str
    model_id: str
    tenant: str
    workspace: str
    input_sources: tuple[str, ...]
    normalization: str
    feature_extraction: tuple[str, ...]
    context_fusion: dict[str, Any]
    confidence: float
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class Attention:
    id: str
    model_id: str
    tenant: str
    workspace: str
    priority: int
    focus_window: int
    context_selection: tuple[str, ...]
    filtering: dict[str, Any]
    scheduling: str


@dataclass(slots=True)
class Memory:
    id: str
    model_id: str
    tenant: str
    workspace: str
    working_memory: dict[str, Any]
    long_term_memory_reference: str
    episodic_memory: tuple[str, ...] = ()
    semantic_memory: tuple[str, ...] = ()
    retention_policy: str = "workspace"
    recall_policy: str = "relevance"


@dataclass(slots=True)
class Reasoning:
    id: str
    model_id: str
    tenant: str
    workspace: str
    mode: ReasoningMode
    premises: tuple[str, ...]
    conclusion: str
    confidence: float
    constraints: tuple[str, ...] = ()
    evidence_references: tuple[str, ...] = ()


@dataclass(slots=True)
class Plan:
    id: str
    model_id: str
    tenant: str
    workspace: str
    goal_decomposition: tuple[str, ...]
    task_graph: dict[str, tuple[str, ...]]
    milestones: tuple[str, ...] = ()
    dependencies: dict[str, tuple[str, ...]] = field(default_factory=dict)
    risk_assessment: dict[str, float] = field(default_factory=dict)
    resource_allocation: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class LearningCycle:
    id: str
    model_id: str
    tenant: str
    workspace: str
    feedback: dict[str, Any]
    reinforcement_signals: dict[str, float]
    outcome_evaluation: dict[str, Any]
    continuous_improvement: tuple[str, ...]
    version_tracking: str


@dataclass(slots=True)
class Reflection:
    id: str
    model_id: str
    tenant: str
    workspace: str
    execution_review: dict[str, Any]
    error_analysis: tuple[str, ...]
    lessons_learned: tuple[str, ...]
    improvement_suggestions: tuple[str, ...]
    confidence_review: float


@dataclass(slots=True)
class Decision:
    id: str
    model_id: str
    tenant: str
    workspace: str
    alternatives: dict[str, float]
    scoring: dict[str, float]
    policy_validation: bool
    approval: str
    execution_plan: str
    selected: str = ""
    evidence_references: tuple[str, ...] = ()


@dataclass(slots=True)
class Adaptation:
    id: str
    model_id: str
    tenant: str
    workspace: str
    policy_adjustment: dict[str, Any]
    threshold_tuning: dict[str, float]
    context_adaptation: dict[str, Any]
    strategy_selection: str


@dataclass(slots=True)
class Monitoring:
    id: str
    model_id: str
    tenant: str
    workspace: str
    health: str
    performance: float
    latency: float
    resource_usage: dict[str, float]
    failure_detection: tuple[str, ...] = ()


@dataclass(slots=True)
class Metacognition:
    id: str
    model_id: str
    tenant: str
    workspace: str
    reasoning_quality: float
    confidence_calibration: float
    bias_detection: tuple[str, ...]
    explainability_reference: str


@dataclass(frozen=True, slots=True)
class AuditEntry:
    action: str
    actor: str
    tenant: str
    workspace: str
    occurred_at: datetime
    metadata: dict[str, Any]


class CognitiveArchitecturePlatform:
    """Secure in-memory reference control plane for cognitive workloads."""

    TRANSITIONS = {
        CognitiveStatus.DRAFT: {CognitiveStatus.TRAINING, CognitiveStatus.ARCHIVED},
        CognitiveStatus.TRAINING: {
            CognitiveStatus.READY,
            CognitiveStatus.PAUSED,
            CognitiveStatus.ARCHIVED,
        },
        CognitiveStatus.READY: {
            CognitiveStatus.RUNNING,
            CognitiveStatus.TRAINING,
            CognitiveStatus.ARCHIVED,
        },
        CognitiveStatus.RUNNING: {CognitiveStatus.PAUSED, CognitiveStatus.READY},
        CognitiveStatus.PAUSED: {
            CognitiveStatus.RUNNING,
            CognitiveStatus.TRAINING,
            CognitiveStatus.ARCHIVED,
        },
        CognitiveStatus.ARCHIVED: {CognitiveStatus.DELETED},
        CognitiveStatus.DELETED: set(),
    }

    def __init__(self) -> None:
        self.models: dict[str, CognitiveModel] = {}
        self.perceptions: list[Perception] = []
        self.attention_records: list[Attention] = []
        self.memories: list[Memory] = []
        self.reasoning_records: list[Reasoning] = []
        self.plans: list[Plan] = []
        self.learning_cycles: list[LearningCycle] = []
        self.reflections: list[Reflection] = []
        self.decisions: list[Decision] = []
        self.adaptations: list[Adaptation] = []
        self.monitoring_records: list[Monitoring] = []
        self.metacognition_records: list[Metacognition] = []
        self.audit: list[AuditEntry] = []
        self.metrics = CognitiveMetrics()

    @staticmethod
    def _check(record: Any, scope: CognitiveScope) -> None:
        if record.tenant != scope.tenant or record.workspace != scope.workspace:
            raise PermissionError("Cross-scope cognitive access denied.")

    @staticmethod
    def _require(scope: CognitiveScope, permission: str) -> None:
        if (
            permission not in scope.permissions
            and "cognitive:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    def _audit(self, action: str, scope: CognitiveScope, **metadata: Any) -> None:
        safe = {
            key: value
            for key, value in metadata.items()
            if not any(term in key.lower() for term in ("secret", "token", "password"))
        }
        self.audit.append(
            AuditEntry(
                action, scope.actor, scope.tenant, scope.workspace, utcnow(), safe
            )
        )

    def _model(self, model_id: str, scope: CognitiveScope) -> CognitiveModel:
        model = self.models[model_id]
        self._check(model, scope)
        return model

    @staticmethod
    def _confidence(value: float) -> None:
        if not 0 <= value <= 1:
            raise ValueError("Confidence must be within [0, 1].")

    def create_model(
        self, model: CognitiveModel, scope: CognitiveScope
    ) -> CognitiveModel:
        self._require(scope, "cognitive:write")
        self._check(model, scope)
        if model.id in self.models or not model.architecture:
            raise ValueError("Model must be unique and define an architecture.")
        self.models[model.id] = model
        self.metrics.increment("cognitive_models_total")
        self._audit("model.create", scope, model_id=model.id)
        return model

    def list_models(self, scope: CognitiveScope) -> list[CognitiveModel]:
        self._require(scope, "cognitive:read")
        return [
            item
            for item in self.models.values()
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def set_status(
        self, model_id: str, status: CognitiveStatus, scope: CognitiveScope
    ) -> CognitiveModel:
        self._require(scope, "cognitive:write")
        model = self._model(model_id, scope)
        if status not in self.TRANSITIONS[model.status]:
            raise ValueError(
                f"Invalid transition: {model.status.value} -> {status.value}"
            )
        model.status = status
        self._audit("model.status", scope, model_id=model_id, status=status.value)
        return model

    def perceive(self, item: Perception, scope: CognitiveScope) -> Perception:
        started = monotonic()
        self._require(scope, "cognitive:execute")
        self._check(item, scope)
        self._model(item.model_id, scope)
        self._confidence(item.confidence)
        if not item.input_sources:
            raise ValueError("Perception requires an input source.")
        self.perceptions.append(item)
        self.metrics.increment("cognitive_latency_seconds", monotonic() - started)
        self._audit("perception.process", scope, perception_id=item.id)
        return item

    def focus(self, item: Attention, scope: CognitiveScope) -> Attention:
        self._require(scope, "cognitive:execute")
        self._check(item, scope)
        self._model(item.model_id, scope)
        if item.priority < 0 or item.focus_window <= 0:
            raise ValueError("Attention priority and focus window are invalid.")
        self.attention_records.append(item)
        self._audit("attention.focus", scope, attention_id=item.id)
        return item

    def remember(self, item: Memory, scope: CognitiveScope) -> Memory:
        self._require(scope, "cognitive:write")
        self._check(item, scope)
        self._model(item.model_id, scope)
        if not item.long_term_memory_reference:
            raise ValueError("Long-term memory must use a reference.")
        self.memories.append(item)
        self._audit("memory.store", scope, memory_id=item.id)
        return item

    def reason(self, item: Reasoning, scope: CognitiveScope) -> Reasoning:
        self._require(scope, "cognitive:reason")
        self._check(item, scope)
        self._model(item.model_id, scope)
        self._confidence(item.confidence)
        if not item.premises or not item.evidence_references:
            raise ValueError("Reasoning requires premises and evidence references.")
        self.reasoning_records.append(item)
        self.metrics.increment("cognitive_reasoning_total")
        self._audit("reasoning.complete", scope, reasoning_id=item.id)
        return item

    def create_plan(self, item: Plan, scope: CognitiveScope) -> Plan:
        self._require(scope, "cognitive:plan")
        self._check(item, scope)
        self._model(item.model_id, scope)
        tasks = set(item.task_graph)
        if not tasks or any(
            not set(dependencies).issubset(tasks)
            for dependencies in item.task_graph.values()
        ):
            raise ValueError("Task graph dependencies must reference defined tasks.")
        if any(not 0 <= risk <= 1 for risk in item.risk_assessment.values()):
            raise ValueError("Plan risks must be within [0, 1].")
        self._topological(item.task_graph)
        self.plans.append(item)
        self._audit("planning.create", scope, plan_id=item.id)
        return item

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
                raise ValueError("Cyclic task graphs are not allowed.")
            for key in ready:
                complete.append(key)
                pending.pop(key)
        return tuple(complete)

    def learn(self, item: LearningCycle, scope: CognitiveScope) -> LearningCycle:
        self._require(scope, "cognitive:learn")
        self._check(item, scope)
        self._model(item.model_id, scope)
        if any(not -1 <= signal <= 1 for signal in item.reinforcement_signals.values()):
            raise ValueError("Reinforcement signals must be within [-1, 1].")
        self.learning_cycles.append(item)
        self.metrics.increment("cognitive_learning_cycles_total")
        self._audit("learning.complete", scope, learning_id=item.id)
        return item

    def reflect(self, item: Reflection, scope: CognitiveScope) -> Reflection:
        self._require(scope, "cognitive:reflect")
        self._check(item, scope)
        self._model(item.model_id, scope)
        self._confidence(item.confidence_review)
        self.reflections.append(item)
        self.metrics.increment("cognitive_reflections_total")
        self._audit("reflection.complete", scope, reflection_id=item.id)
        return item

    def decide(self, item: Decision, scope: CognitiveScope) -> Decision:
        self._require(scope, "cognitive:decide")
        self._check(item, scope)
        self._model(item.model_id, scope)
        if not item.policy_validation or item.approval not in {"approved", "automatic"}:
            self.metrics.increment("cognitive_failures_total")
            raise PermissionError("Decision failed policy validation or approval.")
        if not item.alternatives or set(item.scoring) != set(item.alternatives):
            raise ValueError("Every alternative requires a score.")
        if not item.evidence_references:
            raise ValueError("Decision requires evidence references.")
        item.selected = max(sorted(item.scoring), key=item.scoring.__getitem__)
        self.decisions.append(item)
        self.metrics.increment("cognitive_decisions_total")
        self._audit("decision.complete", scope, decision_id=item.id)
        return item

    def adapt(self, item: Adaptation, scope: CognitiveScope) -> Adaptation:
        self._require(scope, "cognitive:adapt")
        self._check(item, scope)
        self._model(item.model_id, scope)
        if any(not 0 <= value <= 1 for value in item.threshold_tuning.values()):
            raise ValueError("Adaptation thresholds must be within [0, 1].")
        self.adaptations.append(item)
        self._audit("adaptation.apply", scope, adaptation_id=item.id)
        return item

    def monitor(self, item: Monitoring, scope: CognitiveScope) -> Monitoring:
        self._require(scope, "cognitive:monitor")
        self._check(item, scope)
        self._model(item.model_id, scope)
        if item.latency < 0 or any(value < 0 for value in item.resource_usage.values()):
            raise ValueError("Monitoring measurements cannot be negative.")
        self.monitoring_records.append(item)
        if item.failure_detection:
            self.metrics.increment(
                "cognitive_failures_total", len(item.failure_detection)
            )
        self._audit("monitoring.record", scope, monitoring_id=item.id)
        return item

    def evaluate_metacognition(
        self, item: Metacognition, scope: CognitiveScope
    ) -> Metacognition:
        self._require(scope, "cognitive:reflect")
        self._check(item, scope)
        self._model(item.model_id, scope)
        self._confidence(item.reasoning_quality)
        self._confidence(item.confidence_calibration)
        if not item.explainability_reference:
            raise ValueError("Metacognition requires an explainability reference.")
        self.metacognition_records.append(item)
        self._audit("metacognition.evaluate", scope, metacognition_id=item.id)
        return item

    def dashboard(self, scope: CognitiveScope) -> dict[str, Any]:
        self._require(scope, "cognitive:read")

        def scoped(items: list[Any]) -> list[dict[str, Any]]:
            return [
                asdict(item)
                for item in items
                if item.tenant == scope.tenant and item.workspace == scope.workspace
            ]

        models = self.list_models(scope)
        monitoring = scoped(self.monitoring_records)
        return {
            "models": [item.to_dict() for item in models],
            "perception": scoped(self.perceptions),
            "attention": scoped(self.attention_records),
            "memory": scoped(self.memories),
            "reasoning": scoped(self.reasoning_records),
            "planning": scoped(self.plans),
            "learning": scoped(self.learning_cycles),
            "reflection": scoped(self.reflections),
            "decision": scoped(self.decisions),
            "adaptation": scoped(self.adaptations),
            "metacognition": scoped(self.metacognition_records),
            "health": {
                "status": (
                    "degraded"
                    if any(item["failure_detection"] for item in monitoring)
                    else "healthy"
                ),
                "models": len(models),
                "monitoring": monitoring,
            },
            "metrics": self.metrics.snapshot(),
        }


EnterpriseAICognitiveArchitecturePlatform = CognitiveArchitecturePlatform

__all__ = (
    "Adaptation",
    "Attention",
    "AuditEntry",
    "CognitiveArchitecturePlatform",
    "CognitiveModel",
    "CognitiveScope",
    "CognitiveStatus",
    "Decision",
    "EnterpriseAICognitiveArchitecturePlatform",
    "LearningCycle",
    "Memory",
    "Metacognition",
    "Monitoring",
    "Perception",
    "Plan",
    "Reasoning",
    "ReasoningMode",
    "Reflection",
)
