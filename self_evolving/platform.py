"""Governed Enterprise AI Self-Evolving Platform control plane."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from time import monotonic
from typing import Any

from .metrics import SelfEvolvingMetrics


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EvolutionStatus(str, Enum):
    DRAFT = "draft"
    LEARNING = "learning"
    EVALUATING = "evaluating"
    EVOLVING = "evolving"
    VALIDATED = "validated"
    RUNNING = "running"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ApprovalState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    AUTOMATIC = "automatic"


@dataclass(frozen=True, slots=True)
class EvolutionScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"self_evolving:read"})

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class EvolutionProfile:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    generation: int
    capability_level: int
    version: str = "1.0.0"
    status: EvolutionStatus = EvolutionStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class EvolutionCycle:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    capability_evolution: dict[str, Any] = field(default_factory=dict)
    policy_evolution: dict[str, Any] = field(default_factory=dict)
    knowledge_evolution: dict[str, Any] = field(default_factory=dict)
    workflow_evolution: dict[str, Any] = field(default_factory=dict)
    architecture_evolution: dict[str, Any] = field(default_factory=dict)
    parent_version: str = ""
    candidate_version: str = ""
    approval_state: ApprovalState = ApprovalState.PENDING


@dataclass(slots=True)
class LearningCycle:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    continuous_learning: tuple[str, ...]
    outcome_evaluation: dict[str, float]
    experience_replay: tuple[str, ...]
    feedback_integration: dict[str, Any]
    version_tracking: str


@dataclass(slots=True)
class Adaptation:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    context_adaptation: dict[str, Any]
    policy_adaptation: dict[str, Any]
    resource_adaptation: dict[str, float]
    threshold_tuning: dict[str, float]
    strategy_selection: str


@dataclass(slots=True)
class Mutation:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    candidate_variants: tuple[str, ...]
    evaluation: dict[str, float]
    rollback_reference: str
    safety_validated: bool
    controlled: bool = True


@dataclass(slots=True)
class Experiment:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    mode: str
    hypothesis: str
    benchmark: dict[str, float]
    approval_state: ApprovalState
    audit_reference: str
    result: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class Evaluation:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    capability_assessment: dict[str, float]
    regression_analysis: dict[str, float]
    risk_assessment: dict[str, float]
    quality_metrics: dict[str, float]
    confidence: float


@dataclass(slots=True)
class Optimization:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    performance: float
    latency: float
    cost: float
    resource: dict[str, float]
    energy_interface: dict[str, float]
    policy_optimization: dict[str, Any]


@dataclass(slots=True)
class Feedback:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    human_feedback: tuple[str, ...] = ()
    agent_feedback: tuple[str, ...] = ()
    telemetry: dict[str, float] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)
    improvement_actions: tuple[str, ...] = ()


@dataclass(slots=True)
class MonitoringRecord:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    health: str
    evolution_progress: float
    learning_cycles: int
    failures: tuple[str, ...]
    resource_usage: dict[str, float]
    latency: float = 0


@dataclass(frozen=True, slots=True)
class AuditEntry:
    action: str
    actor: str
    tenant: str
    workspace: str
    occurred_at: datetime
    metadata: dict[str, Any]


class SelfEvolvingPlatform:
    """Secure reference control plane for continuously improving AI systems."""

    TRANSITIONS = {
        EvolutionStatus.DRAFT: {EvolutionStatus.LEARNING, EvolutionStatus.ARCHIVED},
        EvolutionStatus.LEARNING: {
            EvolutionStatus.EVALUATING,
            EvolutionStatus.PAUSED,
            EvolutionStatus.ARCHIVED,
        },
        EvolutionStatus.EVALUATING: {
            EvolutionStatus.EVOLVING,
            EvolutionStatus.LEARNING,
            EvolutionStatus.PAUSED,
        },
        EvolutionStatus.EVOLVING: {
            EvolutionStatus.VALIDATED,
            EvolutionStatus.PAUSED,
        },
        EvolutionStatus.VALIDATED: {
            EvolutionStatus.RUNNING,
            EvolutionStatus.LEARNING,
            EvolutionStatus.ARCHIVED,
        },
        EvolutionStatus.RUNNING: {
            EvolutionStatus.LEARNING,
            EvolutionStatus.PAUSED,
        },
        EvolutionStatus.PAUSED: {
            EvolutionStatus.LEARNING,
            EvolutionStatus.RUNNING,
            EvolutionStatus.ARCHIVED,
        },
        EvolutionStatus.ARCHIVED: {EvolutionStatus.DELETED},
        EvolutionStatus.DELETED: set(),
    }
    EXPERIMENT_MODES = {"ab", "shadow", "simulation", "benchmark"}

    def __init__(self) -> None:
        self.profiles: dict[str, EvolutionProfile] = {}
        self.evolution_cycles: list[EvolutionCycle] = []
        self.learning_cycles: list[LearningCycle] = []
        self.adaptations: list[Adaptation] = []
        self.mutations: list[Mutation] = []
        self.experiments: list[Experiment] = []
        self.evaluations: list[Evaluation] = []
        self.optimizations: list[Optimization] = []
        self.feedback_records: list[Feedback] = []
        self.monitoring_records: list[MonitoringRecord] = []
        self.version_lineage: dict[str, str] = {}
        self.audit: list[AuditEntry] = []
        self.kill_switches: set[str] = set()
        self.metrics = SelfEvolvingMetrics()

    @staticmethod
    def _require(scope: EvolutionScope, permission: str) -> None:
        if (
            permission not in scope.permissions
            and "self_evolving:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _check(record: Any, scope: EvolutionScope) -> None:
        if record.tenant != scope.tenant or record.workspace != scope.workspace:
            raise PermissionError("Cross-scope self-evolving access denied.")

    @staticmethod
    def _ratio(value: float, label: str) -> None:
        if not 0 <= value <= 1:
            raise ValueError(f"{label} must be within [0, 1].")

    def _audit(self, action: str, scope: EvolutionScope, **metadata: Any) -> None:
        safe = {
            key: value
            for key, value in metadata.items()
            if not any(
                word in key.lower()
                for word in ("secret", "token", "password", "credential", "key")
            )
        }
        self.audit.append(
            AuditEntry(
                action, scope.actor, scope.tenant, scope.workspace, utcnow(), safe
            )
        )

    def _profile(self, profile_id: str, scope: EvolutionScope) -> EvolutionProfile:
        profile = self.profiles[profile_id]
        self._check(profile, scope)
        return profile

    def _record(
        self,
        item: Any,
        scope: EvolutionScope,
        permission: str,
        target: list[Any],
        action: str,
    ) -> Any:
        self._require(scope, permission)
        self._check(item, scope)
        self._profile(item.profile_id, scope)
        if item.profile_id in self.kill_switches:
            raise RuntimeError("Profile kill switch is active.")
        target.append(item)
        self._audit(action, scope, record_id=item.id, profile_id=item.profile_id)
        return item

    def create_profile(
        self, profile: EvolutionProfile, scope: EvolutionScope
    ) -> EvolutionProfile:
        self._require(scope, "self_evolving:write")
        self._check(profile, scope)
        if profile.id in self.profiles:
            raise ValueError("Profile ID must be unique.")
        if profile.generation < 0 or not 1 <= profile.capability_level <= 5:
            raise ValueError(
                "Generation must be non-negative and capability level within [1, 5]."
            )
        self.profiles[profile.id] = profile
        self.metrics.increment("self_evolving_profiles_total")
        self._audit("profile.create", scope, profile_id=profile.id)
        return profile

    def list_profiles(self, scope: EvolutionScope) -> list[EvolutionProfile]:
        self._require(scope, "self_evolving:read")
        return [
            profile
            for profile in self.profiles.values()
            if profile.tenant == scope.tenant and profile.workspace == scope.workspace
        ]

    def set_status(
        self, profile_id: str, status: EvolutionStatus, scope: EvolutionScope
    ) -> EvolutionProfile:
        self._require(scope, "self_evolving:write")
        profile = self._profile(profile_id, scope)
        if status not in self.TRANSITIONS[profile.status]:
            raise ValueError(
                f"Invalid transition: {profile.status.value} -> {status.value}"
            )
        profile.status = status
        self._audit("profile.status", scope, profile_id=profile_id, status=status.value)
        return profile

    def evolve(self, item: EvolutionCycle, scope: EvolutionScope) -> EvolutionCycle:
        started = monotonic()
        self._require(scope, "self_evolving:evolve")
        if item.approval_state is not ApprovalState.APPROVED:
            raise PermissionError("Evolution requires an approved governance gate.")
        if not item.candidate_version or not item.parent_version:
            raise ValueError("Evolution requires parent and candidate versions.")
        if item.candidate_version in self.version_lineage:
            raise ValueError("Candidate version already exists in lineage.")
        result = self._record(
            item,
            scope,
            "self_evolving:evolve",
            self.evolution_cycles,
            "evolution.complete",
        )
        self.version_lineage[item.candidate_version] = item.parent_version
        profile = self._profile(item.profile_id, scope)
        profile.generation += 1
        profile.version = item.candidate_version
        self.metrics.increment("self_evolution_cycles_total")
        self.metrics.increment("self_latency_seconds", monotonic() - started)
        return result

    def learn(self, item: LearningCycle, scope: EvolutionScope) -> LearningCycle:
        if (
            not item.continuous_learning
            or not item.outcome_evaluation
            or not item.version_tracking
        ):
            raise ValueError(
                "Learning requires sources, outcome evaluation, and version tracking."
            )
        result = self._record(
            item,
            scope,
            "self_evolving:learn",
            self.learning_cycles,
            "learning.complete",
        )
        self.metrics.increment("self_learning_cycles_total")
        return result

    def adapt(self, item: Adaptation, scope: EvolutionScope) -> Adaptation:
        if not item.strategy_selection:
            raise ValueError("Adaptation requires strategy selection.")
        for value in item.threshold_tuning.values():
            self._ratio(value, "Threshold")
        return self._record(
            item, scope, "self_evolving:adapt", self.adaptations, "adaptation.apply"
        )

    def mutate(self, item: Mutation, scope: EvolutionScope) -> Mutation:
        if (
            not item.controlled
            or not item.safety_validated
            or not item.rollback_reference
        ):
            raise PermissionError(
                "Mutation requires controls, safety validation, and rollback."
            )
        if not item.candidate_variants or not item.evaluation:
            raise ValueError("Mutation requires candidate variants and evaluation.")
        return self._record(
            item, scope, "self_evolving:mutate", self.mutations, "mutation.create"
        )

    def experiment(self, item: Experiment, scope: EvolutionScope) -> Experiment:
        if item.mode not in self.EXPERIMENT_MODES:
            raise ValueError("Unsupported experiment mode.")
        if (
            item.approval_state is not ApprovalState.APPROVED
            or not item.audit_reference
        ):
            raise PermissionError(
                "Experiments require approval and an audit reference."
            )
        result = self._record(
            item, scope, "self_evolving:experiment", self.experiments, "experiment.run"
        )
        self.metrics.increment("self_experiments_total")
        return result

    def evaluate(self, item: Evaluation, scope: EvolutionScope) -> Evaluation:
        self._ratio(item.confidence, "Confidence")
        for assessment in (
            item.capability_assessment,
            item.regression_analysis,
            item.risk_assessment,
            item.quality_metrics,
        ):
            for value in assessment.values():
                self._ratio(value, "Assessment")
        return self._record(
            item,
            scope,
            "self_evolving:evaluate",
            self.evaluations,
            "evaluation.complete",
        )

    def optimize(self, item: Optimization, scope: EvolutionScope) -> Optimization:
        if min(item.performance, item.latency, item.cost) < 0:
            raise ValueError("Optimization measurements cannot be negative.")
        result = self._record(
            item,
            scope,
            "self_evolving:optimize",
            self.optimizations,
            "optimization.apply",
        )
        self.metrics.increment("self_optimizations_total")
        return result

    def feedback(self, item: Feedback, scope: EvolutionScope) -> Feedback:
        if not (item.human_feedback or item.agent_feedback or item.telemetry):
            raise ValueError("At least one feedback source is required.")
        return self._record(
            item,
            scope,
            "self_evolving:feedback",
            self.feedback_records,
            "feedback.integrate",
        )

    def monitor(
        self, item: MonitoringRecord, scope: EvolutionScope
    ) -> MonitoringRecord:
        self._ratio(item.evolution_progress, "Evolution progress")
        if (
            item.learning_cycles < 0
            or item.latency < 0
            or any(value < 0 for value in item.resource_usage.values())
        ):
            raise ValueError("Monitoring measurements cannot be negative.")
        return self._record(
            item,
            scope,
            "self_evolving:monitor",
            self.monitoring_records,
            "monitoring.record",
        )

    def activate_kill_switch(
        self, profile_id: str, scope: EvolutionScope, reason: str
    ) -> None:
        self._require(scope, "self_evolving:safety")
        profile = self._profile(profile_id, scope)
        if not reason:
            raise ValueError("Kill switch activation requires a reason.")
        self.kill_switches.add(profile_id)
        if profile.status not in {EvolutionStatus.ARCHIVED, EvolutionStatus.DELETED}:
            profile.status = EvolutionStatus.PAUSED
        self._audit("safety.kill_switch", scope, profile_id=profile_id, reason=reason)

    def release_kill_switch(self, profile_id: str, scope: EvolutionScope) -> None:
        self._require(scope, "self_evolving:safety")
        self._profile(profile_id, scope)
        self.kill_switches.discard(profile_id)
        self._audit("safety.kill_switch_release", scope, profile_id=profile_id)

    def rollback(
        self, profile_id: str, target_version: str, scope: EvolutionScope
    ) -> EvolutionProfile:
        self._require(scope, "self_evolving:rollback")
        profile = self._profile(profile_id, scope)
        ancestors: set[str] = set()
        current = profile.version
        while current in self.version_lineage:
            current = self.version_lineage[current]
            ancestors.add(current)
        if target_version not in ancestors:
            raise ValueError(
                "Rollback target is not an ancestor of the current version."
            )
        profile.version = target_version
        profile.generation = max(0, profile.generation - 1)
        profile.status = EvolutionStatus.PAUSED
        self.metrics.increment("self_rollbacks_total")
        self._audit(
            "evolution.rollback",
            scope,
            profile_id=profile_id,
            target_version=target_version,
        )
        return profile

    def dashboard(self, scope: EvolutionScope) -> dict[str, Any]:
        self._require(scope, "self_evolving:read")

        def scoped(items: list[Any]) -> list[dict[str, Any]]:
            return [
                asdict(item)
                for item in items
                if item.tenant == scope.tenant and item.workspace == scope.workspace
            ]

        monitoring = scoped(self.monitoring_records)
        audit_count = sum(
            entry.tenant == scope.tenant and entry.workspace == scope.workspace
            for entry in self.audit
        )
        return {
            "profiles": [profile.to_dict() for profile in self.list_profiles(scope)],
            "evolution": scoped(self.evolution_cycles),
            "learning": scoped(self.learning_cycles),
            "experiments": scoped(self.experiments),
            "optimization": scoped(self.optimizations),
            "safety": {
                "kill_switches": sorted(
                    profile_id
                    for profile_id in self.kill_switches
                    if self.profiles[profile_id].tenant == scope.tenant
                    and self.profiles[profile_id].workspace == scope.workspace
                ),
                "rollbacks": self.metrics.snapshot()["self_rollbacks_total"],
            },
            "governance": {
                "audit_events": audit_count,
                "approval_gates": True,
                "policy_validation": True,
            },
            "monitoring": {
                "health": "degraded"
                if any(item["failures"] for item in monitoring)
                else "healthy",
                "records": monitoring,
            },
            "metrics": self.metrics.snapshot(),
        }


EnterpriseAISelfEvolvingPlatform = SelfEvolvingPlatform
