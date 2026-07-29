"""Secure, tenant-scoped Enterprise AI Digital Twin control plane."""

from __future__ import annotations

import re
import secrets
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol, TypeVar

from .metrics import DigitalTwinMetrics


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TwinStatus(str, Enum):
    DRAFT = "draft"
    PROVISIONED = "provisioned"
    SYNCHRONIZED = "synchronized"
    RUNNING = "running"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DELETED = "deleted"


class EntityType(str, Enum):
    PERSON = "person"
    DEVICE = "device"
    MACHINE = "machine"
    SYSTEM = "system"
    APPLICATION = "application"
    WORKFLOW = "workflow"
    KNOWLEDGE = "knowledge"
    MODEL = "model"
    CUSTOM = "custom"


class RelationshipType(str, Enum):
    PARENT = "parent"
    CHILD = "child"
    DEPENDENCY = "dependency"
    REFERENCE = "reference"
    OWNERSHIP = "ownership"
    TOPOLOGY = "topology"
    ASSOCIATION = "association"


class SynchronizationMode(str, Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"


class PredictionType(str, Enum):
    CAPACITY = "capacity"
    RISK = "risk"
    FAILURE = "failure"
    USAGE = "usage"
    LATENCY = "latency"
    COST = "cost"


class OptimizationType(str, Enum):
    RESOURCE = "resource"
    EXECUTION = "execution"
    TOPOLOGY = "topology"
    SCHEDULING = "scheduling"
    COST = "cost"
    ENERGY_INTERFACE = "energy_interface"


class Scoped(Protocol):
    id: str
    tenant: str
    workspace: str


ScopedT = TypeVar("ScopedT", bound=Scoped)


@dataclass(frozen=True, slots=True)
class TwinScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"digital_twin:read"})

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class DigitalTwin:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    type: str
    version: str = "1"
    status: TwinStatus = TwinStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        return result


@dataclass(slots=True)
class TwinEntity:
    id: str
    twin_id: str
    tenant: str
    workspace: str
    name: str
    type: EntityType
    attributes: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["type"] = self.type.value
        return result


@dataclass(slots=True)
class TwinRelationship:
    id: str
    twin_id: str
    tenant: str
    workspace: str
    source_id: str
    target_id: str
    type: RelationshipType
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["type"] = self.type.value
        return result


@dataclass(slots=True)
class StateSnapshot:
    id: str
    twin_id: str
    tenant: str
    workspace: str
    version: int
    current_state: dict[str, Any]
    desired_state: dict[str, Any]
    historical_state: dict[str, Any]
    created_at: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["created_at"] = self.created_at.isoformat()
        return result


@dataclass(slots=True)
class SyncPolicy:
    id: str
    twin_id: str
    tenant: str
    workspace: str
    mode: SynchronizationMode
    schedule: str | None = None
    conflict_detection: bool = True
    retry_limit: int = 3
    consistency_validation: bool = True

    def __post_init__(self) -> None:
        if self.retry_limit < 0:
            raise ValueError("Retry limit cannot be negative.")
        if self.mode is SynchronizationMode.SCHEDULED and not self.schedule:
            raise ValueError("Scheduled synchronization requires a schedule.")


@dataclass(slots=True)
class TelemetryRecord:
    id: str
    twin_id: str
    tenant: str
    workspace: str
    metrics: dict[str, float] = field(default_factory=dict)
    logs: tuple[str, ...] = ()
    events: tuple[str, ...] = ()
    health: str = "unknown"
    status: str = "unknown"
    performance: dict[str, float] = field(default_factory=dict)
    capacity: dict[str, float] = field(default_factory=dict)
    recorded_at: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["recorded_at"] = self.recorded_at.isoformat()
        return result


@dataclass(slots=True)
class SimulationRun:
    id: str
    twin_id: str
    tenant: str
    workspace: str
    scenario: dict[str, Any]
    prediction: dict[str, Any]
    impact: dict[str, Any]
    comparison: dict[str, Any]
    rollback_plan: dict[str, Any]
    optimization: dict[str, Any]
    status: str = "completed"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Prediction:
    id: str
    twin_id: str
    tenant: str
    workspace: str
    type: PredictionType
    value: float
    confidence: float
    horizon: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError("Prediction confidence must be between zero and one.")

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["type"] = self.type.value
        return result


@dataclass(slots=True)
class Optimization:
    id: str
    twin_id: str
    tenant: str
    workspace: str
    type: OptimizationType
    recommendation: dict[str, Any]
    expected_improvement: float
    constraints: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["type"] = self.type.value
        return result


@dataclass(frozen=True, slots=True)
class AuditEntry:
    action: str
    actor: str
    tenant: str
    workspace: str
    occurred_at: datetime
    metadata: dict[str, Any]


class DigitalTwinPlatform:
    """Reference control plane; adapters supply external simulation and I/O."""

    TRANSITIONS = {
        TwinStatus.DRAFT: {TwinStatus.PROVISIONED, TwinStatus.ARCHIVED},
        TwinStatus.PROVISIONED: {TwinStatus.SYNCHRONIZED, TwinStatus.ARCHIVED},
        TwinStatus.SYNCHRONIZED: {TwinStatus.RUNNING, TwinStatus.ARCHIVED},
        TwinStatus.RUNNING: {TwinStatus.PAUSED, TwinStatus.ARCHIVED},
        TwinStatus.PAUSED: {TwinStatus.RUNNING, TwinStatus.ARCHIVED},
        TwinStatus.ARCHIVED: {TwinStatus.DELETED},
        TwinStatus.DELETED: set(),
    }
    SECRET_KEYS = re.compile(
        r"(?:password|passwd|secret|token|api[_-]?key|authorization)", re.I
    )

    def __init__(self) -> None:
        self.twins: dict[str, DigitalTwin] = {}
        self.entities: dict[str, TwinEntity] = {}
        self.relationships: dict[str, TwinRelationship] = {}
        self.states: dict[str, list[StateSnapshot]] = {}
        self.sync_policies: dict[str, SyncPolicy] = {}
        self.telemetry: list[TelemetryRecord] = []
        self.simulations: list[SimulationRun] = []
        self.predictions: list[Prediction] = []
        self.optimizations: list[Optimization] = []
        self.audit: list[AuditEntry] = []
        self.metrics = DigitalTwinMetrics()

    @staticmethod
    def _in_scope(record: Any, scope: TwinScope) -> bool:
        return bool(
            record.tenant == scope.tenant and record.workspace == scope.workspace
        )

    @staticmethod
    def _require(scope: TwinScope, permission: str) -> None:
        if (
            permission not in scope.permissions
            and "digital_twin:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    def _get(
        self, records: dict[str, ScopedT], record_id: str, scope: TwinScope
    ) -> ScopedT:
        record = records[record_id]
        if not self._in_scope(record, scope):
            raise PermissionError("Cross-tenant or cross-workspace access denied.")
        return record

    def _audit(self, action: str, scope: TwinScope, **metadata: Any) -> None:
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

    def _validate_safe(self, value: Any) -> None:
        if isinstance(value, dict):
            if any(self.SECRET_KEYS.search(str(key)) for key in value):
                raise ValueError("Secrets are not allowed in digital-twin data.")
            for item in value.values():
                self._validate_safe(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                self._validate_safe(item)

    def create_twin(self, twin: DigitalTwin, scope: TwinScope) -> DigitalTwin:
        self._require(scope, "digital_twin:write")
        if not self._in_scope(twin, scope):
            raise PermissionError("Cross-tenant or cross-workspace write denied.")
        if twin.id in self.twins:
            raise ValueError("Digital twin already exists.")
        self._validate_safe(twin.metadata)
        self.twins[twin.id] = twin
        self.metrics.increment("digital_twins_total")
        self._audit("twin.create", scope, twin_id=twin.id)
        return twin

    def set_status(
        self, twin_id: str, status: TwinStatus, scope: TwinScope
    ) -> DigitalTwin:
        self._require(scope, "digital_twin:write")
        twin = self._get(self.twins, twin_id, scope)
        if status not in self.TRANSITIONS[twin.status]:
            raise ValueError("Invalid digital-twin lifecycle transition.")
        twin.status = status
        self._audit("twin.status", scope, twin_id=twin_id, status=status.value)
        return twin

    def add_entity(self, entity: TwinEntity, scope: TwinScope) -> TwinEntity:
        self._require(scope, "digital_twin:write")
        self._get(self.twins, entity.twin_id, scope)
        if not self._in_scope(entity, scope):
            raise PermissionError("Cross-tenant or cross-workspace write denied.")
        if entity.id in self.entities:
            raise ValueError("Entity already exists.")
        self._validate_safe(entity.attributes)
        self.entities[entity.id] = entity
        self._audit("entity.create", scope, entity_id=entity.id)
        return entity

    def add_relationship(
        self, relationship: TwinRelationship, scope: TwinScope
    ) -> TwinRelationship:
        self._require(scope, "digital_twin:write")
        self._get(self.twins, relationship.twin_id, scope)
        source = self._get(self.entities, relationship.source_id, scope)
        target = self._get(self.entities, relationship.target_id, scope)
        if (
            source.twin_id != relationship.twin_id
            or target.twin_id != relationship.twin_id
        ):
            raise ValueError("Relationships cannot cross digital twins.")
        if relationship.source_id == relationship.target_id:
            raise ValueError("Self-referential relationships are not allowed.")
        if relationship.id in self.relationships:
            raise ValueError("Relationship already exists.")
        self.relationships[relationship.id] = relationship
        self._audit("relationship.create", scope, relationship_id=relationship.id)
        return relationship

    def topology(self, twin_id: str, scope: TwinScope) -> dict[str, Any]:
        self._require(scope, "digital_twin:read")
        self._get(self.twins, twin_id, scope)
        return {
            "entities": [
                item.to_dict()
                for item in self.entities.values()
                if item.twin_id == twin_id and self._in_scope(item, scope)
            ],
            "relationships": [
                item.to_dict()
                for item in self.relationships.values()
                if item.twin_id == twin_id and self._in_scope(item, scope)
            ],
        }

    def set_state(
        self,
        twin_id: str,
        current_state: dict[str, Any],
        desired_state: dict[str, Any],
        scope: TwinScope,
        *,
        expected_version: int | None = None,
    ) -> StateSnapshot:
        self._require(scope, "digital_twin:state")
        self._get(self.twins, twin_id, scope)
        self._validate_safe(current_state)
        self._validate_safe(desired_state)
        history = self.states.setdefault(twin_id, [])
        version = len(history) + 1
        if expected_version is not None and expected_version != len(history):
            raise ValueError("State conflict detected.")
        previous = history[-1].current_state if history else {}
        snapshot = StateSnapshot(
            secrets.token_hex(12),
            twin_id,
            scope.tenant,
            scope.workspace,
            version,
            dict(current_state),
            dict(desired_state),
            dict(previous),
        )
        history.append(snapshot)
        self._audit("state.update", scope, twin_id=twin_id, version=version)
        return snapshot

    def state_diff(
        self, twin_id: str, older: int, newer: int, scope: TwinScope
    ) -> dict[str, dict[str, Any]]:
        self._require(scope, "digital_twin:read")
        self._get(self.twins, twin_id, scope)
        history = self.states[twin_id]
        before = history[older - 1].current_state
        after = history[newer - 1].current_state
        keys = before.keys() | after.keys()
        return {
            key: {"before": before.get(key), "after": after.get(key)}
            for key in keys
            if before.get(key) != after.get(key)
        }

    def configure_sync(self, policy: SyncPolicy, scope: TwinScope) -> SyncPolicy:
        self._require(scope, "digital_twin:sync")
        self._get(self.twins, policy.twin_id, scope)
        if not self._in_scope(policy, scope):
            raise PermissionError("Cross-tenant or cross-workspace write denied.")
        self.sync_policies[policy.id] = policy
        self._audit("sync.configure", scope, policy_id=policy.id)
        return policy

    def synchronize(
        self,
        twin_id: str,
        observed_state: dict[str, Any],
        scope: TwinScope,
        *,
        expected_version: int | None = None,
    ) -> StateSnapshot:
        self._require(scope, "digital_twin:sync")
        try:
            history = self.states.get(twin_id, [])
            desired = history[-1].desired_state if history else observed_state
            elevated = TwinScope(
                scope.tenant,
                scope.workspace,
                scope.actor,
                scope.permissions | {"digital_twin:state"},
            )
            snapshot = self.set_state(
                twin_id,
                observed_state,
                desired,
                elevated,
                expected_version=expected_version,
            )
            self.metrics.increment("twin_sync_total")
            self._audit("sync.complete", scope, twin_id=twin_id)
            return snapshot
        except Exception:
            self.metrics.increment("twin_sync_failures_total")
            self._audit("sync.failed", scope, twin_id=twin_id)
            raise

    def record_telemetry(
        self, record: TelemetryRecord, scope: TwinScope
    ) -> TelemetryRecord:
        self._require(scope, "digital_twin:telemetry")
        self._get(self.twins, record.twin_id, scope)
        if not self._in_scope(record, scope):
            raise PermissionError("Cross-tenant or cross-workspace write denied.")
        self._validate_safe(record.to_dict())
        self.telemetry.append(record)
        return record

    def run_simulation(
        self,
        twin_id: str,
        scenario: dict[str, Any],
        scope: TwinScope,
        *,
        rollback_plan: dict[str, Any] | None = None,
    ) -> SimulationRun:
        self._require(scope, "digital_twin:simulate")
        self._get(self.twins, twin_id, scope)
        self._validate_safe(scenario)
        latest = self.states.get(twin_id, [])
        baseline = latest[-1].current_state if latest else {}
        impact = {
            key: {"before": baseline.get(key), "after": value}
            for key, value in scenario.items()
            if baseline.get(key) != value
        }
        run = SimulationRun(
            secrets.token_hex(12),
            twin_id,
            scope.tenant,
            scope.workspace,
            dict(scenario),
            {"outcome": "projected", "confidence": 0.75},
            impact,
            {"baseline": baseline, "scenario": scenario},
            rollback_plan or {"action": "restore_latest_snapshot"},
            {"recommendation": "review projected impact"},
        )
        self.simulations.append(run)
        self.metrics.increment("simulation_runs_total")
        self._audit("simulation.run", scope, twin_id=twin_id, run_id=run.id)
        return run

    def add_prediction(self, prediction: Prediction, scope: TwinScope) -> Prediction:
        self._require(scope, "digital_twin:predict")
        self._get(self.twins, prediction.twin_id, scope)
        if not self._in_scope(prediction, scope):
            raise PermissionError("Cross-tenant or cross-workspace write denied.")
        self._validate_safe(prediction.evidence)
        self.predictions.append(prediction)
        self.metrics.increment("prediction_total")
        self._audit("prediction.create", scope, prediction_id=prediction.id)
        return prediction

    def add_optimization(
        self, optimization: Optimization, scope: TwinScope
    ) -> Optimization:
        self._require(scope, "digital_twin:optimize")
        self._get(self.twins, optimization.twin_id, scope)
        if not self._in_scope(optimization, scope):
            raise PermissionError("Cross-tenant or cross-workspace write denied.")
        self._validate_safe(optimization.recommendation)
        self.optimizations.append(optimization)
        self.metrics.increment("optimization_total")
        self._audit("optimization.create", scope, optimization_id=optimization.id)
        return optimization

    def dashboard(self, scope: TwinScope) -> dict[str, Any]:
        self._require(scope, "digital_twin:read")

        def scoped(values: Any) -> list[Any]:
            return [item for item in values if self._in_scope(item, scope)]

        twins = scoped(self.twins.values())
        twin_ids = {item.id for item in twins}
        return {
            "twins": [item.to_dict() for item in twins],
            "topology": {
                twin_id: self.topology(twin_id, scope) for twin_id in twin_ids
            },
            "telemetry": [item.to_dict() for item in scoped(self.telemetry)],
            "simulation": [item.to_dict() for item in scoped(self.simulations)],
            "predictions": [item.to_dict() for item in scoped(self.predictions)],
            "optimization": [item.to_dict() for item in scoped(self.optimizations)],
            "metrics": self.metrics.snapshot(),
        }


EnterpriseAIDigitalTwinPlatform = DigitalTwinPlatform
