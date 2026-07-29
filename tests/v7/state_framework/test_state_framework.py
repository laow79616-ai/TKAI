from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from tkai.v7.security import AccessController, Principal
from tkai.v7.state_framework import (
    IllegalTransitionError,
    Lifecycle,
    StateFramework,
    StateRecord,
    StateScope,
    StateSecurity,
    StateValidationError,
    VersionConflictError,
)
from tkai.v7.state_framework.api import STATE_RESOURCES, register_state_framework_routes
from tkai.v7.state_framework.dashboard import StateDashboard
from tkai.v7.state_framework.persistence import MemoryStatePersistence
from tkai.v7.state_framework.registry import StateRegistry


def state(
    state_id: str = "state-1",
    *,
    dependencies: tuple[str, ...] = (),
) -> StateRecord:
    return StateRecord(
        state_id=state_id,
        state_type="component",
        owner="kernel",
        version=1,
        lifecycle=Lifecycle.CREATED,
        current_state="new",
        previous_state=None,
        scope=StateScope("tenant-1", "workspace-1"),
        metadata={"token": "sensitive", "label": "safe"},
        dependencies=dependencies,
    )


def test_registry_and_persistence_are_explicit() -> None:
    persistence = MemoryStatePersistence()
    framework = StateFramework(StateRegistry(persistence))
    registered = framework.register(state())
    assert framework.registry.get("state-1") == registered
    assert persistence.load("state-1") == registered
    with pytest.raises(StateValidationError):
        framework.register(state())


def test_state_model_is_immutable_and_filters_secrets() -> None:
    model = state()
    assert model.metadata["token"] == "[REDACTED]"
    with pytest.raises(FrozenInstanceError):
        model.version = 2  # type: ignore[misc]


def test_lifecycle_and_deterministic_transition() -> None:
    framework = StateFramework()
    framework.register(state())
    updated = framework.transition(
        "state-1", "initialized", Lifecycle.INITIALIZED, expected_version=1
    )
    assert updated.version == 2
    assert updated.previous_state == "new"
    assert len(updated.transition_history) == 1


def test_illegal_and_stale_transitions_are_rejected() -> None:
    framework = StateFramework()
    framework.register(state())
    with pytest.raises(IllegalTransitionError):
        framework.transition(
            "state-1", "running", Lifecycle.RUNNING, expected_version=1
        )
    with pytest.raises(VersionConflictError):
        framework.transition(
            "state-1", "initialized", Lifecycle.INITIALIZED, expected_version=2
        )
    assert framework.metrics.snapshot()["v7_state_illegal_transitions_total"] == 1


def test_version_aware_compatibility_transition() -> None:
    framework = StateFramework()
    framework.register(state())
    framework.allow_compatibility_transition("new", "legacy-ready", 1, 2)
    updated = framework.transition(
        "state-1",
        "legacy-ready",
        Lifecycle.READY,
        expected_version=1,
        compatibility=True,
    )
    assert updated.lifecycle is Lifecycle.READY
    assert framework.transitions[0].compatibility


def test_snapshot_is_immutable_versioned_reference_only_and_valid() -> None:
    framework = StateFramework()
    framework.register(state())
    snapshot = framework.create_snapshot("state-1", "memory://state-1/v1")
    assert snapshot.state_version == 1
    assert snapshot.verify()
    assert snapshot.metadata["token"] == "[REDACTED]"
    with pytest.raises(ValueError):
        framework.create_snapshot("state-1", "inline payload")
    with pytest.raises(FrozenInstanceError):
        snapshot.state_version = 2  # type: ignore[misc]


def test_history_metrics_audit_and_tracing() -> None:
    framework = StateFramework()
    traces: list[tuple[str, object]] = []
    framework.tracing.register(lambda name, attrs: traces.append((name, attrs)))
    framework.register(state(), actor="operator")
    framework.transition(
        "state-1", "initialized", Lifecycle.INITIALIZED, expected_version=1
    )
    projection = framework.snapshot()
    assert projection["history"]
    assert projection["audit"]
    assert projection["metrics"]["v7_state_transitions_total"] == 1
    assert [item[0] for item in traces] == [
        "state.registered",
        "state.transitioned",
    ]


def test_consistency_validates_dependencies_and_references() -> None:
    framework = StateFramework()
    framework.register(state(dependencies=("missing",)))
    report = framework.validate("state-1")
    assert not report.valid
    assert report.issues[0].code == "dependency_missing"
    framework.registry.replace(
        replace(framework.registry.get("state-1"), snapshot_reference="not-found")
    )
    codes = {issue.code for issue in framework.validate("state-1").issues}
    assert "snapshot_reference_missing" in codes


def test_recovery_is_validation_only_and_never_mutates_state() -> None:
    framework = StateFramework()
    original = framework.register(state())
    snapshot = framework.create_snapshot("state-1", "memory://state-1/v1")
    before = framework.registry.get("state-1")
    plan = framework.simulate_recovery("state-1", snapshot.snapshot_id)
    after = framework.registry.get("state-1")
    assert plan.ready and plan.simulated
    assert before == after
    assert original.current_state == after.current_state


def test_security_enforces_rbac_tenant_and_workspace_isolation() -> None:
    access = AccessController({"operator": {"state.transition"}})
    framework = StateFramework(security=StateSecurity(access))
    framework.register(state())
    principal = Principal("operator-1", frozenset({"operator"}))
    with pytest.raises(PermissionError, match="tenant"):
        framework.transition(
            "state-1",
            "initialized",
            Lifecycle.INITIALIZED,
            expected_version=1,
            principal=principal,
            tenant_reference="other",
        )
    with pytest.raises(PermissionError, match="lacks"):
        framework.transition(
            "state-1",
            "initialized",
            Lifecycle.INITIALIZED,
            expected_version=1,
            principal=Principal("viewer", frozenset({"viewer"})),
        )


class FakeApp:
    def __init__(self) -> None:
        self.routes: list[tuple[str, object, tuple[str, ...]]] = []

    def add_api_route(
        self, path: str, endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        self.routes.append((path, endpoint, tuple(methods)))


def test_api_is_get_only_and_complete() -> None:
    app = FakeApp()
    register_state_framework_routes(app, StateFramework())
    assert {path for path, _, _ in app.routes} == {
        f"/v7/state/{resource}" for resource in STATE_RESOURCES
    }
    assert all(methods == ("GET",) for _, _, methods in app.routes)


def test_dashboard_has_all_required_sections() -> None:
    dashboard = StateDashboard(StateFramework())
    assert set(dashboard.snapshot()) == set(dashboard.sections)
