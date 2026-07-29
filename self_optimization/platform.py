"""Governed Enterprise AI Self-Optimization Platform control plane."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from time import monotonic
from typing import Any

from .metrics import SelfOptimizationMetrics


class OptimizationStatus(str, Enum):
    DRAFT = "draft"
    ANALYZING = "analyzing"
    OPTIMIZING = "optimizing"
    VALIDATING = "validating"
    RUNNING = "running"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DELETED = "deleted"


class StrategyType(str, Enum):
    RULE_BASED = "rule_based"
    HEURISTIC = "heuristic"
    PREDICTIVE = "predictive"
    ADAPTIVE = "adaptive"
    AI_ASSISTED = "ai_assisted"
    HYBRID = "hybrid"


class ApprovalState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    AUTOMATIC = "automatic"


@dataclass(frozen=True, slots=True)
class OptimizationScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"self_optimization:read"})

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class OptimizationProfile:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    optimization_target: str
    version: str = "1.0.0"
    status: OptimizationStatus = OptimizationStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class OptimizationCycle:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    strategy: StrategyType
    performance_improvement: float = 0
    latency_improvement: float = 0
    cost_reduction: float = 0
    capacity_adjustment: float = 0
    resource_optimization: dict[str, float] = field(default_factory=dict)
    policy_optimization: dict[str, Any] = field(default_factory=dict)
    parent_version: str = ""
    candidate_version: str = ""
    approval_state: ApprovalState = ApprovalState.PENDING
    rollback_reference: str = ""


@dataclass(slots=True)
class ResourcePlan:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    cpu: float = 0
    memory: float = 0
    storage: float = 0
    network: float = 0
    gpu: float = 0
    queue: float = 0
    concurrency: int = 0


@dataclass(slots=True)
class PerformanceRecord:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    throughput: float
    response_time: float
    utilization: float
    efficiency: float
    bottlenecks: tuple[str, ...] = ()
    trend_analysis: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class CostRecord:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    resource_cost: float
    execution_cost: float
    storage_cost: float
    network_cost: float
    budget_target: float
    savings_estimation: float


@dataclass(slots=True)
class LatencyRecord:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    average: float
    p95: float
    p99: float
    tail_latency: float
    optimization_actions: tuple[str, ...] = ()


@dataclass(slots=True)
class CapacityPlan:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    forecast: float
    scaling_recommendation: str
    utilization_threshold: float
    auto_scaling_policy: dict[str, Any]
    reserve_capacity: float


@dataclass(slots=True)
class Experiment:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    mode: str
    approval_state: ApprovalState
    rollback_reference: str
    result: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class Recommendation:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    priority: str
    expected_benefit: float
    risk: float
    confidence: float
    execution_plan: tuple[str, ...]


@dataclass(slots=True)
class Evaluation:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    benchmark: dict[str, float]
    regression_analysis: dict[str, float]
    quality_metrics: dict[str, float]
    risk_assessment: float
    confidence: float


@dataclass(slots=True)
class MonitoringRecord:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    health: str
    optimization_cycles: int
    failures: tuple[str, ...]
    resource_usage: dict[str, float]
    performance_trends: dict[str, float]


@dataclass(frozen=True, slots=True)
class AuditEntry:
    action: str
    actor: str
    tenant: str
    workspace: str
    occurred_at: datetime
    metadata: dict[str, Any]


class SelfOptimizationPlatform:
    """Secure control plane for measurable, reversible optimization."""

    TRANSITIONS = {
        OptimizationStatus.DRAFT: {
            OptimizationStatus.ANALYZING,
            OptimizationStatus.ARCHIVED,
        },
        OptimizationStatus.ANALYZING: {
            OptimizationStatus.OPTIMIZING,
            OptimizationStatus.PAUSED,
        },
        OptimizationStatus.OPTIMIZING: {
            OptimizationStatus.VALIDATING,
            OptimizationStatus.PAUSED,
        },
        OptimizationStatus.VALIDATING: {
            OptimizationStatus.RUNNING,
            OptimizationStatus.OPTIMIZING,
            OptimizationStatus.PAUSED,
        },
        OptimizationStatus.RUNNING: {
            OptimizationStatus.ANALYZING,
            OptimizationStatus.PAUSED,
        },
        OptimizationStatus.PAUSED: {
            OptimizationStatus.ANALYZING,
            OptimizationStatus.RUNNING,
            OptimizationStatus.ARCHIVED,
        },
        OptimizationStatus.ARCHIVED: {OptimizationStatus.DELETED},
        OptimizationStatus.DELETED: set(),
    }
    EXPERIMENT_MODES = {"simulation", "canary", "shadow", "ab"}

    def __init__(self, risk_threshold: float = 0.5) -> None:
        self._ratio(risk_threshold, "Risk threshold")
        self.risk_threshold = risk_threshold
        self.profiles: dict[str, OptimizationProfile] = {}
        self.cycles: list[OptimizationCycle] = []
        self.resources: list[ResourcePlan] = []
        self.performance: list[PerformanceRecord] = []
        self.costs: list[CostRecord] = []
        self.latencies: list[LatencyRecord] = []
        self.capacities: list[CapacityPlan] = []
        self.experiments: list[Experiment] = []
        self.recommendations: list[Recommendation] = []
        self.evaluations: list[Evaluation] = []
        self.monitoring_records: list[MonitoringRecord] = []
        self.version_lineage: dict[str, str] = {}
        self.audit: list[AuditEntry] = []
        self.kill_switches: set[str] = set()
        self.metrics = SelfOptimizationMetrics()

    @staticmethod
    def _ratio(value: float, label: str) -> None:
        if not 0 <= value <= 1:
            raise ValueError(f"{label} must be within [0, 1].")

    @staticmethod
    def _require(scope: OptimizationScope, permission: str) -> None:
        if (
            permission not in scope.permissions
            and "self_optimization:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _check(record: Any, scope: OptimizationScope) -> None:
        if record.tenant != scope.tenant or record.workspace != scope.workspace:
            raise PermissionError("Cross-scope self-optimization access denied.")

    def _audit(self, action: str, scope: OptimizationScope, **metadata: Any) -> None:
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
                action,
                scope.actor,
                scope.tenant,
                scope.workspace,
                datetime.now(timezone.utc),
                safe,
            )
        )

    def _profile(
        self, profile_id: str, scope: OptimizationScope
    ) -> OptimizationProfile:
        profile = self.profiles[profile_id]
        self._check(profile, scope)
        return profile

    def _record(
        self,
        item: Any,
        scope: OptimizationScope,
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
        self, profile: OptimizationProfile, scope: OptimizationScope
    ) -> OptimizationProfile:
        self._require(scope, "self_optimization:write")
        self._check(profile, scope)
        if not profile.id or not profile.name or not profile.optimization_target:
            raise ValueError("Profile ID, name, and optimization target are required.")
        if profile.id in self.profiles:
            raise ValueError("Profile ID must be unique.")
        self.profiles[profile.id] = profile
        self.metrics.increment("self_optimization_profiles_total")
        self._audit("profile.create", scope, profile_id=profile.id)
        return profile

    def list_profiles(self, scope: OptimizationScope) -> list[OptimizationProfile]:
        self._require(scope, "self_optimization:read")
        return [
            item
            for item in self.profiles.values()
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def set_status(
        self,
        profile_id: str,
        status: OptimizationStatus,
        scope: OptimizationScope,
    ) -> OptimizationProfile:
        self._require(scope, "self_optimization:write")
        profile = self._profile(profile_id, scope)
        if status not in self.TRANSITIONS[profile.status]:
            raise ValueError(
                f"Invalid transition: {profile.status.value} -> {status.value}"
            )
        profile.status = status
        self._audit("profile.status", scope, profile_id=profile_id, status=status.value)
        return profile

    def optimize(
        self, item: OptimizationCycle, scope: OptimizationScope
    ) -> OptimizationCycle:
        started = monotonic()
        if item.approval_state is not ApprovalState.APPROVED:
            raise PermissionError("Optimization requires an approved governance gate.")
        if not item.rollback_reference:
            raise PermissionError("Optimization requires a rollback reference.")
        values = (
            item.performance_improvement,
            item.latency_improvement,
            item.cost_reduction,
            item.capacity_adjustment,
            *item.resource_optimization.values(),
        )
        if any(value < 0 for value in values):
            raise ValueError("Optimization measurements cannot be negative.")
        if not item.parent_version or not item.candidate_version:
            raise ValueError("Optimization requires parent and candidate versions.")
        if item.candidate_version in self.version_lineage:
            raise ValueError("Candidate version already exists in lineage.")
        result = self._record(
            item,
            scope,
            "self_optimization:optimize",
            self.cycles,
            "optimization.complete",
        )
        self.version_lineage[item.candidate_version] = item.parent_version
        self._profile(item.profile_id, scope).version = item.candidate_version
        self.metrics.increment("self_optimization_cycles_total")
        metric_values = (
            ("self_performance_improvements_total", item.performance_improvement),
            ("self_latency_improvements_total", item.latency_improvement),
            ("self_cost_reduction_total", item.cost_reduction),
            ("self_capacity_adjustments_total", item.capacity_adjustment),
        )
        for name, value in metric_values:
            self.metrics.increment(name, value)
        self.metrics.increment(
            "self_optimization_latency_seconds", monotonic() - started
        )
        return result

    def record_resource(
        self, item: ResourcePlan, scope: OptimizationScope
    ) -> ResourcePlan:
        values = (
            item.cpu,
            item.memory,
            item.storage,
            item.network,
            item.gpu,
            item.queue,
            item.concurrency,
        )
        if any(value < 0 for value in values):
            raise ValueError("Resource values cannot be negative.")
        return self._record(
            item,
            scope,
            "self_optimization:resources",
            self.resources,
            "resources.plan",
        )

    def record_performance(
        self, item: PerformanceRecord, scope: OptimizationScope
    ) -> PerformanceRecord:
        self._ratio(item.utilization, "Utilization")
        self._ratio(item.efficiency, "Efficiency")
        if item.throughput < 0 or item.response_time < 0:
            raise ValueError("Performance values cannot be negative.")
        return self._record(
            item,
            scope,
            "self_optimization:performance",
            self.performance,
            "performance.record",
        )

    def record_cost(self, item: CostRecord, scope: OptimizationScope) -> CostRecord:
        if any(
            value < 0
            for value in (
                item.resource_cost,
                item.execution_cost,
                item.storage_cost,
                item.network_cost,
                item.budget_target,
                item.savings_estimation,
            )
        ):
            raise ValueError("Cost values cannot be negative.")
        return self._record(
            item, scope, "self_optimization:cost", self.costs, "cost.record"
        )

    def record_latency(
        self, item: LatencyRecord, scope: OptimizationScope
    ) -> LatencyRecord:
        if min(item.average, item.p95, item.p99, item.tail_latency) < 0:
            raise ValueError("Latency values cannot be negative.")
        if not item.average <= item.p95 <= item.p99 <= item.tail_latency:
            raise ValueError("Latency percentiles must be monotonic.")
        return self._record(
            item, scope, "self_optimization:latency", self.latencies, "latency.record"
        )

    def plan_capacity(
        self, item: CapacityPlan, scope: OptimizationScope
    ) -> CapacityPlan:
        self._ratio(item.utilization_threshold, "Utilization threshold")
        if item.forecast < 0 or item.reserve_capacity < 0:
            raise ValueError("Capacity values cannot be negative.")
        return self._record(
            item,
            scope,
            "self_optimization:capacity",
            self.capacities,
            "capacity.plan",
        )

    def experiment(self, item: Experiment, scope: OptimizationScope) -> Experiment:
        if item.mode not in self.EXPERIMENT_MODES:
            raise ValueError("Unsupported experiment mode.")
        if (
            item.approval_state is not ApprovalState.APPROVED
            or not item.rollback_reference
        ):
            raise PermissionError("Experiments require approval and rollback.")
        return self._record(
            item,
            scope,
            "self_optimization:experiment",
            self.experiments,
            "experiment.run",
        )

    def recommend(
        self, item: Recommendation, scope: OptimizationScope
    ) -> Recommendation:
        self._ratio(item.risk, "Risk")
        self._ratio(item.confidence, "Confidence")
        if item.risk > self.risk_threshold:
            raise PermissionError(
                "Recommendation exceeds the configured risk threshold."
            )
        if item.expected_benefit < 0 or not item.execution_plan:
            raise ValueError("Recommendation requires benefit and an execution plan.")
        return self._record(
            item,
            scope,
            "self_optimization:recommend",
            self.recommendations,
            "recommendation.create",
        )

    def evaluate(self, item: Evaluation, scope: OptimizationScope) -> Evaluation:
        self._ratio(item.risk_assessment, "Risk assessment")
        self._ratio(item.confidence, "Confidence")
        if not item.benchmark or not item.quality_metrics:
            raise ValueError("Evaluation requires benchmark and quality metrics.")
        return self._record(
            item,
            scope,
            "self_optimization:evaluate",
            self.evaluations,
            "evaluation.complete",
        )

    def monitor(
        self, item: MonitoringRecord, scope: OptimizationScope
    ) -> MonitoringRecord:
        if item.optimization_cycles < 0 or any(
            value < 0 for value in item.resource_usage.values()
        ):
            raise ValueError("Monitoring measurements cannot be negative.")
        return self._record(
            item,
            scope,
            "self_optimization:monitor",
            self.monitoring_records,
            "monitoring.record",
        )

    def activate_kill_switch(
        self, profile_id: str, scope: OptimizationScope, reason: str
    ) -> None:
        self._require(scope, "self_optimization:safety")
        profile = self._profile(profile_id, scope)
        if not reason:
            raise ValueError("Kill switch activation requires a reason.")
        self.kill_switches.add(profile_id)
        if profile.status not in {
            OptimizationStatus.ARCHIVED,
            OptimizationStatus.DELETED,
        }:
            profile.status = OptimizationStatus.PAUSED
        self._audit("safety.kill_switch", scope, profile_id=profile_id, reason=reason)

    def release_kill_switch(self, profile_id: str, scope: OptimizationScope) -> None:
        self._require(scope, "self_optimization:safety")
        self._profile(profile_id, scope)
        self.kill_switches.discard(profile_id)
        self._audit("safety.kill_switch_release", scope, profile_id=profile_id)

    def rollback(
        self, profile_id: str, target_version: str, scope: OptimizationScope
    ) -> OptimizationProfile:
        self._require(scope, "self_optimization:rollback")
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
        profile.status = OptimizationStatus.PAUSED
        self._audit(
            "optimization.rollback",
            scope,
            profile_id=profile_id,
            target_version=target_version,
        )
        return profile

    def dashboard(self, scope: OptimizationScope) -> dict[str, Any]:
        self._require(scope, "self_optimization:read")

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
            "profiles": [item.to_dict() for item in self.list_profiles(scope)],
            "optimization": scoped(self.cycles),
            "resources": scoped(self.resources),
            "performance": scoped(self.performance),
            "cost": scoped(self.costs),
            "latency": scoped(self.latencies),
            "capacity": scoped(self.capacities),
            "experiments": scoped(self.experiments),
            "recommendations": scoped(self.recommendations),
            "monitoring": {
                "health": (
                    "degraded"
                    if any(item["failures"] for item in monitoring)
                    else "healthy"
                ),
                "records": monitoring,
            },
            "governance": {
                "audit_events": audit_count,
                "approval_gates": True,
                "policy_validation": True,
                "tenant_isolation": True,
                "workspace_isolation": True,
            },
            "safety": {
                "kill_switches": sorted(
                    profile_id
                    for profile_id in self.kill_switches
                    if self.profiles[profile_id].tenant == scope.tenant
                    and self.profiles[profile_id].workspace == scope.workspace
                ),
                "risk_threshold": self.risk_threshold,
                "rollback": True,
                "human_oversight": True,
            },
            "evaluation": scoped(self.evaluations),
            "metrics": self.metrics.snapshot(),
        }


EnterpriseAISelfOptimizationPlatform = SelfOptimizationPlatform
