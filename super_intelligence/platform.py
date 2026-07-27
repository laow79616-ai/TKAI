"""Governed Enterprise AI Super Intelligence control plane."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from time import monotonic
from typing import Any, TypeVar

from .metrics import SuperIntelligenceMetrics


class IntelligenceStatus(str, Enum):
    DRAFT = "draft"
    TRAINING = "training"
    LEARNING = "learning"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass(frozen=True, slots=True)
class IntelligenceScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"super_intelligence:read"})

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
    architecture: str
    version: str = "1.0.0"
    status: IntelligenceStatus = IntelligenceStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class Capability:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    name: str
    level: int
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CollectiveReasoning:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    distributed_reasoning: tuple[str, ...]
    evidence_fusion: tuple[str, ...]
    consensus: str
    conflict_resolution: str
    confidence: float
    decision_trace_reference: str


@dataclass(slots=True)
class StrategicPlan:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    mission: str
    objectives: tuple[str, ...]
    milestones: tuple[str, ...]
    dependencies: dict[str, tuple[str, ...]]
    resource_allocation: dict[str, float]
    scenario_planning: tuple[str, ...]
    risk_analysis: dict[str, float]


@dataclass(slots=True)
class WorldModel:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    environment_model: dict[str, Any]
    system_model: dict[str, Any]
    business_model: dict[str, Any]
    digital_twin_reference: str
    simulation: dict[str, Any]
    forecast: dict[str, float]


@dataclass(slots=True)
class KnowledgeSynthesis:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    knowledge_graph_reference: str
    semantic_integration: tuple[str, ...]
    evidence_references: tuple[str, ...]
    cross_domain_linking: dict[str, tuple[str, ...]]
    knowledge_evolution: str


@dataclass(slots=True)
class Prediction:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    risk_prediction: dict[str, float]
    capacity_forecast: dict[str, float]
    outcome_prediction: dict[str, float]
    trend_forecast: dict[str, float]
    confidence_calibration: float


@dataclass(slots=True)
class Optimization:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    resource_optimization: dict[str, float]
    cost_optimization: dict[str, float]
    latency_optimization: dict[str, float]
    energy_optimization: dict[str, float]
    policy_optimization: dict[str, Any]


@dataclass(slots=True)
class Coordination:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    agents: tuple[str, ...]
    task_delegation: dict[str, str]
    negotiation: str
    shared_memory_reference: str
    consensus: str


@dataclass(slots=True)
class Decision:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    evidence: tuple[str, ...]
    policy_validated: bool
    approval_gates: tuple[str, ...]
    execution_plan: tuple[str, ...]
    rollback_strategy: str


@dataclass(slots=True)
class Adaptation:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    dynamic_strategy: str
    context_awareness: dict[str, Any]
    threshold_adjustment: dict[str, float]
    fallback: str
    continuous_adaptation: bool


@dataclass(slots=True)
class SelfImprovement:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    performance_review: dict[str, float]
    learning_feedback: dict[str, Any]
    capability_evolution: tuple[str, ...]
    model_version_tracking: str
    improvement_recommendations: tuple[str, ...]


@dataclass(slots=True)
class Alignment:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    business_goals: tuple[str, ...]
    safety_policies: tuple[str, ...]
    compliance: tuple[str, ...]
    ethics: tuple[str, ...]
    human_oversight: str
    audit_reference: str


@dataclass(slots=True)
class Evaluation:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    benchmarking: dict[str, float]
    capability_assessment: dict[str, float]
    confidence: float
    quality_metrics: dict[str, float]
    regression_analysis: dict[str, float]


@dataclass(slots=True)
class MonitoringRecord:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    health: str
    latency: float
    resource_usage: dict[str, float]
    failures: tuple[str, ...]
    capability_trends: dict[str, tuple[float, ...]]
    audit_reference: str


@dataclass(frozen=True, slots=True)
class AuditEntry:
    action: str
    actor: str
    tenant: str
    workspace: str
    occurred_at: datetime
    metadata: dict[str, Any]


Record = TypeVar("Record")


class SuperIntelligencePlatform:
    """Tenant-isolated, policy-governed reference control plane."""

    CAPABILITIES = (
        "Strategic Reasoning",
        "Scientific Reasoning",
        "Collective Intelligence",
        "Knowledge Synthesis",
        "Cross-domain Learning",
        "Autonomous Coordination",
        "Long-horizon Planning",
        "Adaptive Optimization",
    )
    TRANSITIONS = {
        IntelligenceStatus.DRAFT: {
            IntelligenceStatus.TRAINING,
            IntelligenceStatus.ARCHIVED,
        },
        IntelligenceStatus.TRAINING: {
            IntelligenceStatus.LEARNING,
            IntelligenceStatus.PAUSED,
        },
        IntelligenceStatus.LEARNING: {
            IntelligenceStatus.READY,
            IntelligenceStatus.PAUSED,
        },
        IntelligenceStatus.READY: {
            IntelligenceStatus.RUNNING,
            IntelligenceStatus.LEARNING,
        },
        IntelligenceStatus.RUNNING: {
            IntelligenceStatus.PAUSED,
            IntelligenceStatus.COMPLETED,
        },
        IntelligenceStatus.PAUSED: {
            IntelligenceStatus.TRAINING,
            IntelligenceStatus.LEARNING,
            IntelligenceStatus.RUNNING,
            IntelligenceStatus.ARCHIVED,
        },
        IntelligenceStatus.COMPLETED: {IntelligenceStatus.ARCHIVED},
        IntelligenceStatus.ARCHIVED: {IntelligenceStatus.DELETED},
        IntelligenceStatus.DELETED: set(),
    }

    def __init__(self) -> None:
        self.profiles: dict[str, IntelligenceProfile] = {}
        self.capabilities: list[Capability] = []
        self.reasoning_records: list[CollectiveReasoning] = []
        self.plans: list[StrategicPlan] = []
        self.world_models: list[WorldModel] = []
        self.knowledge_records: list[KnowledgeSynthesis] = []
        self.predictions: list[Prediction] = []
        self.optimizations: list[Optimization] = []
        self.coordination_records: list[Coordination] = []
        self.decisions: list[Decision] = []
        self.adaptations: list[Adaptation] = []
        self.improvements: list[SelfImprovement] = []
        self.alignments: list[Alignment] = []
        self.evaluations: list[Evaluation] = []
        self.monitoring_records: list[MonitoringRecord] = []
        self.audit: list[AuditEntry] = []
        self.metrics = SuperIntelligenceMetrics()

    @staticmethod
    def _check(record: Any, scope: IntelligenceScope) -> None:
        if record.tenant != scope.tenant or record.workspace != scope.workspace:
            raise PermissionError("Cross-scope super intelligence access denied.")

    @staticmethod
    def _require(scope: IntelligenceScope, permission: str) -> None:
        if (
            permission not in scope.permissions
            and "super_intelligence:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _confidence(value: float) -> None:
        if not 0 <= value <= 1:
            raise ValueError("Confidence must be within [0, 1].")

    @staticmethod
    def _ratios(values: dict[str, float]) -> None:
        if any(not 0 <= value <= 1 for value in values.values()):
            raise ValueError("Ratio values must be within [0, 1].")

    def _audit(self, action: str, scope: IntelligenceScope, **metadata: Any) -> None:
        blocked = ("secret", "token", "password", "credential", "key")
        safe = {
            key: value
            for key, value in metadata.items()
            if not any(term in key.lower() for term in blocked)
        }
        self.audit.append(
            AuditEntry(
                action,
                scope.actor,
                scope.tenant,
                scope.workspace,
                datetime.now(timezone.utc),
                safe,
            )
        )

    def _profile(
        self, profile_id: str, scope: IntelligenceScope
    ) -> IntelligenceProfile:
        profile = self.profiles[profile_id]
        self._check(profile, scope)
        return profile

    def _record(
        self,
        item: Record,
        scope: IntelligenceScope,
        permission: str,
        records: list[Record],
        action: str,
    ) -> Record:
        self._require(scope, permission)
        self._check(item, scope)
        self._profile(item.profile_id, scope)  # type: ignore[attr-defined]
        records.append(item)
        self._audit(action, scope, record_id=item.id, profile_id=item.profile_id)  # type: ignore[attr-defined]
        return item

    def create_profile(
        self, profile: IntelligenceProfile, scope: IntelligenceScope
    ) -> IntelligenceProfile:
        self._require(scope, "super_intelligence:write")
        self._check(profile, scope)
        if profile.id in self.profiles:
            raise ValueError("Profile ID must be unique.")
        if not 1 <= profile.capability_level <= 5 or not profile.architecture:
            raise ValueError(
                "Capability level must be within [1, 5] and architecture is required."
            )
        self.profiles[profile.id] = profile
        self.metrics.increment("super_intelligence_profiles_total")
        self._audit("profile.create", scope, profile_id=profile.id)
        return profile

    def list_profiles(self, scope: IntelligenceScope) -> list[IntelligenceProfile]:
        self._require(scope, "super_intelligence:read")
        return [
            item
            for item in self.profiles.values()
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def set_status(
        self, profile_id: str, status: IntelligenceStatus, scope: IntelligenceScope
    ) -> IntelligenceProfile:
        self._require(scope, "super_intelligence:write")
        profile = self._profile(profile_id, scope)
        if status not in self.TRANSITIONS[profile.status]:
            raise ValueError(
                f"Invalid transition: {profile.status.value} -> {status.value}"
            )
        profile.status = status
        self._audit("profile.status", scope, profile_id=profile_id, status=status.value)
        return profile

    def register_capability(
        self, item: Capability, scope: IntelligenceScope
    ) -> Capability:
        if item.name not in self.CAPABILITIES or not 1 <= item.level <= 5:
            raise ValueError("Unsupported capability or invalid level.")
        return self._record(
            item,
            scope,
            "super_intelligence:write",
            self.capabilities,
            "capability.register",
        )

    def reason(
        self, item: CollectiveReasoning, scope: IntelligenceScope
    ) -> CollectiveReasoning:
        started = monotonic()
        self._confidence(item.confidence)
        if (
            not item.distributed_reasoning
            or not item.evidence_fusion
            or not item.consensus
            or not item.decision_trace_reference
        ):
            raise ValueError(
                "Collective reasoning requires evidence, consensus, "
                "and a decision trace."
            )
        result = self._record(
            item,
            scope,
            "super_intelligence:reason",
            self.reasoning_records,
            "reasoning.complete",
        )
        self.metrics.increment("super_reasoning_total")
        self.metrics.increment("super_latency_seconds", monotonic() - started)
        return result

    def plan(self, item: StrategicPlan, scope: IntelligenceScope) -> StrategicPlan:
        if not item.mission or not item.objectives or not item.milestones:
            raise ValueError(
                "Strategic plans require a mission, objectives, and milestones."
            )
        self._ratios(item.risk_analysis)
        known = set(item.milestones)
        if any(not set(deps).issubset(known) for deps in item.dependencies.values()):
            raise ValueError("Dependencies must reference known milestones.")
        return self._record(
            item, scope, "super_intelligence:plan", self.plans, "planning.create"
        )

    def model_world(self, item: WorldModel, scope: IntelligenceScope) -> WorldModel:
        if (
            not item.environment_model
            or not item.system_model
            or not item.business_model
            or not item.digital_twin_reference
        ):
            raise ValueError(
                "World models require environment, system, business, "
                "and digital twin models."
            )
        return self._record(
            item,
            scope,
            "super_intelligence:model",
            self.world_models,
            "world_model.create",
        )

    def synthesize(
        self, item: KnowledgeSynthesis, scope: IntelligenceScope
    ) -> KnowledgeSynthesis:
        if not item.knowledge_graph_reference or not item.evidence_references:
            raise ValueError(
                "Knowledge synthesis requires graph and evidence references."
            )
        return self._record(
            item,
            scope,
            "super_intelligence:synthesize",
            self.knowledge_records,
            "knowledge.synthesize",
        )

    def predict(self, item: Prediction, scope: IntelligenceScope) -> Prediction:
        self._confidence(item.confidence_calibration)
        self._ratios(item.risk_prediction)
        result = self._record(
            item,
            scope,
            "super_intelligence:predict",
            self.predictions,
            "prediction.complete",
        )
        self.metrics.increment("super_predictions_total")
        return result

    def optimize(self, item: Optimization, scope: IntelligenceScope) -> Optimization:
        if not item.policy_optimization:
            raise ValueError("Policy optimization is required.")
        result = self._record(
            item,
            scope,
            "super_intelligence:optimize",
            self.optimizations,
            "optimization.complete",
        )
        self.metrics.increment("super_optimizations_total")
        return result

    def coordinate(self, item: Coordination, scope: IntelligenceScope) -> Coordination:
        if not item.agents or not item.shared_memory_reference or not item.consensus:
            raise ValueError(
                "Coordination requires agents, shared memory, and consensus."
            )
        if not set(item.task_delegation.values()).issubset(item.agents):
            raise ValueError("Delegations must target participating agents.")
        return self._record(
            item,
            scope,
            "super_intelligence:coordinate",
            self.coordination_records,
            "coordination.complete",
        )

    def decide(self, item: Decision, scope: IntelligenceScope) -> Decision:
        if (
            not item.evidence
            or not item.policy_validated
            or not item.execution_plan
            or not item.rollback_strategy
        ):
            raise PermissionError(
                "Decisions require evidence, policy validation, "
                "execution, and rollback."
            )
        if item.approval_gates:
            self._require(scope, "super_intelligence:approve")
        return self._record(
            item,
            scope,
            "super_intelligence:decide",
            self.decisions,
            "decision.approved",
        )

    def adapt(self, item: Adaptation, scope: IntelligenceScope) -> Adaptation:
        self._ratios(item.threshold_adjustment)
        if (
            not item.dynamic_strategy
            or not item.fallback
            or not item.continuous_adaptation
        ):
            raise ValueError(
                "Continuous adaptation requires primary and fallback strategies."
            )
        return self._record(
            item,
            scope,
            "super_intelligence:adapt",
            self.adaptations,
            "adaptation.complete",
        )

    def self_improve(
        self, item: SelfImprovement, scope: IntelligenceScope
    ) -> SelfImprovement:
        if not item.model_version_tracking or not item.improvement_recommendations:
            raise ValueError(
                "Self improvement requires model tracking and recommendations."
            )
        result = self._record(
            item,
            scope,
            "super_intelligence:improve",
            self.improvements,
            "self_improvement.complete",
        )
        self.metrics.increment("super_self_improvements_total")
        return result

    def align(self, item: Alignment, scope: IntelligenceScope) -> Alignment:
        if (
            not item.business_goals
            or not item.safety_policies
            or not item.human_oversight
            or not item.audit_reference
        ):
            raise PermissionError(
                "Alignment requires goals, safety policy, human oversight, and audit."
            )
        return self._record(
            item,
            scope,
            "super_intelligence:align",
            self.alignments,
            "alignment.validate",
        )

    def evaluate(self, item: Evaluation, scope: IntelligenceScope) -> Evaluation:
        self._confidence(item.confidence)
        self._ratios(item.capability_assessment)
        result = self._record(
            item,
            scope,
            "super_intelligence:evaluate",
            self.evaluations,
            "evaluation.complete",
        )
        self.metrics.increment("super_evaluations_total")
        return result

    def monitor(
        self, item: MonitoringRecord, scope: IntelligenceScope
    ) -> MonitoringRecord:
        if item.latency < 0 or not item.audit_reference:
            raise ValueError("Monitoring latency must be non-negative and audited.")
        result = self._record(
            item,
            scope,
            "super_intelligence:monitor",
            self.monitoring_records,
            "monitoring.record",
        )
        self.metrics.increment("super_latency_seconds", item.latency)
        return result

    def dashboard(self, scope: IntelligenceScope) -> dict[str, Any]:
        self._require(scope, "super_intelligence:read")

        def scoped(items: list[Any]) -> list[dict[str, Any]]:
            return [
                asdict(item)
                for item in items
                if item.tenant == scope.tenant and item.workspace == scope.workspace
            ]

        monitoring = scoped(self.monitoring_records)
        return {
            "profiles": [item.to_dict() for item in self.list_profiles(scope)],
            "capabilities": scoped(self.capabilities),
            "reasoning": scoped(self.reasoning_records),
            "planning": scoped(self.plans),
            "world-models": scoped(self.world_models),
            "knowledge": scoped(self.knowledge_records),
            "prediction": scoped(self.predictions),
            "optimization": scoped(self.optimizations),
            "coordination": scoped(self.coordination_records),
            "decision": scoped(self.decisions),
            "adaptation": scoped(self.adaptations),
            "self-improvement": scoped(self.improvements),
            "alignment": scoped(self.alignments),
            "evaluation": scoped(self.evaluations),
            "monitoring": {
                "health": "degraded"
                if any(item["failures"] for item in monitoring)
                else "healthy",
                "records": monitoring,
                "audit_events": sum(
                    entry.tenant == scope.tenant and entry.workspace == scope.workspace
                    for entry in self.audit
                ),
            },
            "metrics": self.metrics.snapshot(),
        }


EnterpriseAISuperIntelligencePlatform = SuperIntelligencePlatform
