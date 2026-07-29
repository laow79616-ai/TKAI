"""Local-only V7 Unified State Management Framework."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace
from threading import RLock
from uuid import uuid4

from tkai.v7.security import AccessController, Principal, filter_secrets

from .contracts import (
    HistoryEntry,
    Lifecycle,
    RecoveryPlan,
    Snapshot,
    StatePersistence,
    StateRecord,
    Transition,
    ValidationIssue,
    ValidationReport,
    serialize,
    utc_now,
)

LIFECYCLE_TRANSITIONS: Mapping[Lifecycle, frozenset[Lifecycle]] = {
    Lifecycle.CREATED: frozenset({Lifecycle.INITIALIZED, Lifecycle.DELETED}),
    Lifecycle.INITIALIZED: frozenset({Lifecycle.READY, Lifecycle.DELETED}),
    Lifecycle.READY: frozenset(
        {Lifecycle.RUNNING, Lifecycle.RECOVERING, Lifecycle.STOPPING}
    ),
    Lifecycle.RUNNING: frozenset(
        {Lifecycle.PAUSED, Lifecycle.RECOVERING, Lifecycle.STOPPING}
    ),
    Lifecycle.PAUSED: frozenset(
        {Lifecycle.RUNNING, Lifecycle.RECOVERING, Lifecycle.STOPPING}
    ),
    Lifecycle.RECOVERING: frozenset({Lifecycle.READY, Lifecycle.STOPPING}),
    Lifecycle.STOPPING: frozenset({Lifecycle.STOPPED}),
    Lifecycle.STOPPED: frozenset(
        {Lifecycle.READY, Lifecycle.RECOVERING, Lifecycle.ARCHIVED}
    ),
    Lifecycle.ARCHIVED: frozenset({Lifecycle.DELETED}),
    Lifecycle.DELETED: frozenset(),
}

METRIC_NAMES = (
    "v7_state_registered_total",
    "v7_state_transitions_total",
    "v7_state_illegal_transitions_total",
    "v7_state_snapshots_total",
    "v7_state_validations_total",
    "v7_state_consistency_failures_total",
    "v7_state_recovery_simulations_total",
)


class StateFrameworkError(RuntimeError):
    pass


class StateValidationError(StateFrameworkError):
    pass


class IllegalTransitionError(StateFrameworkError):
    pass


class VersionConflictError(StateFrameworkError):
    pass


class Metrics:
    def __init__(self) -> None:
        self._values = {name: 0.0 for name in METRIC_NAMES}

    def increment(self, name: str, amount: float = 1.0) -> None:
        self._values[name] += amount

    def snapshot(self) -> dict[str, float]:
        return dict(self._values)


class TracingHooks:
    def __init__(self) -> None:
        self._hooks: list[Callable[[str, Mapping[str, object]], None]] = []

    def register(self, hook: Callable[[str, Mapping[str, object]], None]) -> None:
        self._hooks.append(hook)

    def emit(self, name: str, attributes: Mapping[str, object]) -> None:
        safe = filter_secrets(attributes)
        for hook in self._hooks:
            hook(name, safe)


class StateSecurity:
    def __init__(self, access: AccessController | None = None) -> None:
        self.access = access

    def authorize(
        self,
        principal: Principal | None,
        capability: str,
        state: StateRecord,
        *,
        tenant_reference: str | None = None,
        workspace_reference: str | None = None,
        owner: str | None = None,
    ) -> None:
        if self.access is not None:
            if principal is None:
                raise PermissionError("principal required")
            self.access.require(principal, capability)
        if tenant_reference and state.scope.tenant_reference != tenant_reference:
            raise PermissionError("tenant isolation violation")
        if (
            workspace_reference
            and state.scope.workspace_reference != workspace_reference
        ):
            raise PermissionError("workspace isolation violation")
        if owner and state.owner != owner:
            raise PermissionError("state owner isolation violation")


class StateRegistry:
    def __init__(self, persistence: StatePersistence | None = None) -> None:
        self._states: dict[str, StateRecord] = {}
        self._lock = RLock()
        self.persistence = persistence

    def register(self, state: StateRecord) -> StateRecord:
        with self._lock:
            if state.state_id in self._states:
                raise StateValidationError(
                    f"state already registered: {state.state_id}"
                )
            self._states[state.state_id] = state
            if self.persistence:
                self.persistence.save(state)
            return state

    def get(self, state_id: str) -> StateRecord:
        try:
            return self._states[state_id]
        except KeyError as error:
            raise KeyError(f"unknown state: {state_id}") from error

    def replace(self, state: StateRecord) -> StateRecord:
        with self._lock:
            if state.state_id not in self._states:
                raise KeyError(f"unknown state: {state.state_id}")
            self._states[state.state_id] = state
            if self.persistence:
                self.persistence.save(state)
            return state

    def list(self) -> tuple[StateRecord, ...]:
        return tuple(self._states[key] for key in sorted(self._states))


class StateFramework:
    """Explicit state operations; recovery and rollback never mutate automatically."""

    def __init__(
        self,
        registry: StateRegistry | None = None,
        *,
        security: StateSecurity | None = None,
    ) -> None:
        self.registry = registry or StateRegistry()
        self.security = security or StateSecurity()
        self.metrics = Metrics()
        self.tracing = TracingHooks()
        self.transitions: list[Transition] = []
        self.snapshots: dict[str, Snapshot] = {}
        self.history: list[HistoryEntry] = []
        self.recoveries: list[RecoveryPlan] = []
        self.logs: list[dict[str, object]] = []
        self.compatibility_transitions: set[tuple[str, str, int, int]] = set()

    def _history(
        self,
        state_id: str,
        category: str,
        action: str,
        actor: str,
        *,
        reference: str | None = None,
        details: Mapping[str, object] | None = None,
    ) -> HistoryEntry:
        entry = HistoryEntry(
            str(uuid4()),
            state_id,
            category,
            action,
            actor,
            reference,
            filter_secrets(details or {}),
        )
        self.history.append(entry)
        self.logs.append(
            {
                "timestamp": entry.timestamp,
                "level": "info",
                "event": f"state.{action}",
                "state_id": state_id,
                "category": category,
                "actor": actor,
                "reference": reference,
                "details": filter_secrets(details or {}),
            }
        )
        return entry

    def register(self, state: StateRecord, *, actor: str = "system") -> StateRecord:
        result = self.registry.register(state)
        self.metrics.increment("v7_state_registered_total")
        self._history(state.state_id, "audit", "registered", actor)
        self.tracing.emit("state.registered", {"state_id": state.state_id})
        return result

    def allow_compatibility_transition(
        self, from_state: str, to_state: str, from_version: int, to_version: int
    ) -> None:
        self.compatibility_transitions.add(
            (from_state, to_state, from_version, to_version)
        )

    def transition(
        self,
        state_id: str,
        to_state: str,
        to_lifecycle: Lifecycle,
        *,
        expected_version: int,
        actor: str = "system",
        reason: str = "",
        compatibility: bool = False,
        principal: Principal | None = None,
        tenant_reference: str | None = None,
        workspace_reference: str | None = None,
    ) -> StateRecord:
        state = self.registry.get(state_id)
        self.security.authorize(
            principal,
            "state.transition",
            state,
            tenant_reference=tenant_reference,
            workspace_reference=workspace_reference,
        )
        if state.version != expected_version:
            raise VersionConflictError(
                f"expected version {expected_version}, found {state.version}"
            )
        version_key = (state.current_state, to_state, state.version, state.version + 1)
        lifecycle_valid = to_lifecycle in LIFECYCLE_TRANSITIONS[state.lifecycle]
        compatible = compatibility and version_key in self.compatibility_transitions
        if not lifecycle_valid and not compatible:
            self.metrics.increment("v7_state_illegal_transitions_total")
            raise IllegalTransitionError(
                f"illegal transition: {state.lifecycle.value} -> {to_lifecycle.value}"
            )
        transition = Transition(
            str(uuid4()),
            state_id,
            state.current_state,
            to_state,
            state.lifecycle,
            to_lifecycle,
            state.version,
            state.version + 1,
            actor,
            reason,
            compatible,
        )
        updated = replace(
            state,
            version=state.version + 1,
            lifecycle=to_lifecycle,
            previous_state=state.current_state,
            current_state=to_state,
            transition_history=(*state.transition_history, transition.transition_id),
            updated_at=utc_now(),
        )
        self.registry.replace(updated)
        self.transitions.append(transition)
        self.metrics.increment("v7_state_transitions_total")
        self._history(
            state_id,
            "transition",
            "transitioned",
            actor,
            reference=transition.transition_id,
        )
        self._history(state_id, "lifecycle", to_lifecycle.value, actor)
        self.tracing.emit(
            "state.transitioned",
            {"state_id": state_id, "transition_id": transition.transition_id},
        )
        return updated

    def create_snapshot(
        self, state_id: str, state_reference: str, *, actor: str = "system"
    ) -> Snapshot:
        state = self.registry.get(state_id)
        snapshot = Snapshot.create(state, state_reference, actor)
        self.snapshots[snapshot.snapshot_id] = snapshot
        self.registry.replace(
            replace(
                state,
                snapshot_reference=snapshot.snapshot_id,
                updated_at=utc_now(),
            )
        )
        self.metrics.increment("v7_state_snapshots_total")
        self._history(
            state_id,
            "snapshot",
            "created",
            actor,
            reference=snapshot.snapshot_id,
        )
        return snapshot

    def validate(self, state_id: str) -> ValidationReport:
        state = self.registry.get(state_id)
        issues: list[ValidationIssue] = []
        if state.previous_state is not None and not state.transition_history:
            issues.append(
                ValidationIssue(
                    "transition_history_missing",
                    "previous state requires transition history",
                    state_id,
                )
            )
        if state.snapshot_reference:
            snapshot = self.snapshots.get(state.snapshot_reference)
            if snapshot is None:
                issues.append(
                    ValidationIssue(
                        "snapshot_reference_missing",
                        "snapshot reference is not registered",
                        state_id,
                    )
                )
            elif not snapshot.verify():
                issues.append(
                    ValidationIssue(
                        "snapshot_integrity_invalid",
                        "snapshot integrity validation failed",
                        state_id,
                    )
                )
            elif snapshot.state_version > state.version:
                issues.append(
                    ValidationIssue(
                        "version_integrity_invalid",
                        "snapshot version is newer than state",
                        state_id,
                    )
                )
        known = {item.state_id for item in self.registry.list()}
        for dependency in state.dependencies:
            if dependency not in known:
                issues.append(
                    ValidationIssue(
                        "dependency_missing",
                        f"dependency is not registered: {dependency}",
                        state_id,
                    )
                )
        report = ValidationReport(state_id, not issues, tuple(issues))
        self.metrics.increment("v7_state_validations_total")
        if issues:
            self.metrics.increment("v7_state_consistency_failures_total")
        return report

    def validate_all(self) -> tuple[ValidationReport, ...]:
        return tuple(self.validate(state.state_id) for state in self.registry.list())

    def simulate_recovery(
        self, state_id: str, snapshot_id: str, *, actor: str = "system"
    ) -> RecoveryPlan:
        state = self.registry.get(state_id)
        snapshot = self.snapshots.get(snapshot_id)
        issues: list[str] = []
        if snapshot is None:
            issues.append("snapshot not found")
            target_version = state.version
        else:
            target_version = snapshot.state_version
            if snapshot.state_id != state_id:
                issues.append("snapshot state mismatch")
            if not snapshot.verify():
                issues.append("snapshot integrity invalid")
            if snapshot.state_version > state.version:
                issues.append("snapshot version is newer than current state")
        plan = RecoveryPlan(
            str(uuid4()),
            state_id,
            snapshot_id,
            target_version,
            ready=not issues,
            valid=not issues,
            issues=tuple(issues),
        )
        self.recoveries.append(plan)
        self.metrics.increment("v7_state_recovery_simulations_total")
        self._history(
            state_id,
            "recovery",
            "simulated",
            actor,
            reference=plan.recovery_id,
            details={"ready": plan.ready, "issues": plan.issues},
        )
        return plan

    simulate_rollback = simulate_recovery

    def restore_snapshot(self, state_id: str, snapshot_id: str) -> StateRecord:
        """Build a validated restoration candidate without changing the registry."""
        state = self.registry.get(state_id)
        plan = self.simulate_recovery(state_id, snapshot_id)
        if not plan.ready:
            raise StateValidationError("; ".join(plan.issues))
        snapshot = self.snapshots[snapshot_id]
        return replace(
            state,
            version=snapshot.state_version,
            lifecycle=snapshot.lifecycle,
            current_state=snapshot.current_state,
            previous_state=snapshot.previous_state,
            snapshot_reference=snapshot.snapshot_id,
        )

    def snapshot(self) -> dict[str, object]:
        states = self.registry.list()
        validations = self.validate_all()
        history = tuple(self.history)
        return {
            "registry": serialize(states),
            "lifecycle": serialize(
                tuple(
                    {"state_id": state.state_id, "lifecycle": state.lifecycle}
                    for state in states
                )
            ),
            "transitions": serialize(tuple(self.transitions)),
            "snapshots": serialize(tuple(self.snapshots.values())),
            "history": serialize(history),
            "consistency": serialize(validations),
            "recovery": serialize(tuple(self.recoveries)),
            "health": {
                "status": (
                    "healthy"
                    if all(report.valid for report in validations)
                    else "degraded"
                ),
                "states": len(states),
                "invalid_states": sum(not report.valid for report in validations),
            },
            "metrics": self.metrics.snapshot(),
            "audit": serialize(history),
        }


GLOBAL_STATE_FRAMEWORK = StateFramework()

__all__ = (
    "GLOBAL_STATE_FRAMEWORK",
    "IllegalTransitionError",
    "LIFECYCLE_TRANSITIONS",
    "METRIC_NAMES",
    "Metrics",
    "StateFramework",
    "StateFrameworkError",
    "StateRegistry",
    "StateSecurity",
    "StateValidationError",
    "TracingHooks",
    "VersionConflictError",
)
