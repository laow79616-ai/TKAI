"""Offline mock-only tests for the V10 Sovereign Recovery Mesh."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from tkai.v10.contracts import Scope
from tkai.v10.recovery_mesh import (
    RecoveryDependency,
    RecoveryPlan,
    RecoveryPlanStatus,
    RecoveryProfile,
    RecoveryReadiness,
    RecoveryReadinessStatus,
    RecoveryStrategy,
    RecoveryStrategyType,
    RecoveryValidation,
    RecoveryValidationType,
    SovereignRecoveryMesh,
)
from tkai.v10.recovery_mesh.api import GET_ROUTES, openapi_contract, register_routes
from tkai.v10.recovery_mesh.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v10.recovery_mesh.security import authorize_metadata_read


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def add_api_route(
        self, path: str, handler: object, *, methods: list[str], **_: object
    ) -> None:
        self.routes[path] = (methods[0], handler)


def test_structure_profile_and_generation_compatibility() -> None:
    root = Path(__file__).resolve().parents[3]
    assert root.resolve() == Path(r"C:\Users\laow7\Documents\TKAI").resolve()
    required = set(
        """profiles registry contexts strategies plans dependencies readiness
validation compatibility governance integrity trust operations planning decision reasoning
knowledge diagnostics health metrics audit security events contracts interfaces lifecycle
dashboard api""".split()  # noqa: E501
    )
    package = root / "src/tkai/v10/recovery_mesh"
    assert required <= {path.name for path in package.iterdir() if path.is_dir()}
    profile = RecoveryProfile("profile", "subject", safe_metadata={"label": "safe"})
    with pytest.raises(FrozenInstanceError):
        profile.health = "bad"  # type: ignore[misc]
    mesh = SovereignRecoveryMesh()
    mesh.register("profiles", profile)
    assert {item.generation for item in mesh.discover("compatibility")} == {
        "v6",
        "v7",
        "v8",
        "v9",
        "v10",
    }


def test_strategies_are_reference_only_and_non_executable() -> None:
    mesh = SovereignRecoveryMesh()
    for index, kind in enumerate(RecoveryStrategyType):
        strategy = RecoveryStrategy(f"s-{index}", "subject", kind)
        mesh.register("strategies", strategy)
        assert strategy.reference_only and not strategy.executable
    assert len(mesh.discover("strategies")) == 5


def test_plans_are_metadata_only_and_non_executable() -> None:
    mesh = SovereignRecoveryMesh()
    for index, status in enumerate(RecoveryPlanStatus):
        plan = RecoveryPlan(f"p-{index}", "subject", status)
        mesh.register("plans", plan)
        assert plan.metadata_only and not plan.executable
    assert len(mesh.discover("plans")) == 5


def test_readiness_never_triggers_recovery() -> None:
    mesh = SovereignRecoveryMesh()
    for index, status in enumerate(RecoveryReadinessStatus):
        readiness = RecoveryReadiness(f"r-{index}", "subject", status)
        mesh.register("readiness", readiness)
        assert readiness.metadata_only and not readiness.triggers_recovery
    assert len(mesh.discover("readiness")) == 5


def test_all_validation_types_and_dependencies_are_metadata_only() -> None:
    mesh = SovereignRecoveryMesh()
    dependency = RecoveryDependency("dependency", "subject", ("required",))
    mesh.register("dependencies", dependency)
    assert dependency.reference_only
    for index, kind in enumerate(RecoveryValidationType):
        validation = RecoveryValidation(f"v-{index}", "subject", kind)
        mesh.register("validation", validation)
        assert validation.metadata_only
    assert len(mesh.discover("validation")) == 6


def test_bounds_rbac_isolation_and_secret_filtering() -> None:
    mesh = SovereignRecoveryMesh(per_registry_limit=5)
    scope = Scope("tenant", "workspace")
    authorize_metadata_read(scope, scope, role_references=("reader",))
    with pytest.raises(PermissionError):
        authorize_metadata_read(scope, scope)
    with pytest.raises(PermissionError):
        authorize_metadata_read(
            scope, Scope("other", "workspace"), role_references=("reader",)
        )
    with pytest.raises(ValueError, match="hidden"):
        mesh.register(
            "profiles",
            RecoveryProfile(
                "bad", "subject", safe_metadata={"chain_of_thought": "secret"}
            ),
        )
    assert mesh.serialize({"api_key": "secret"}) == {"api_key": "[REDACTED]"}
    with pytest.raises(ValueError, match="between 0 and 100"):
        mesh.discover("profiles", limit=101)


def test_dashboard_health_metrics_audit_and_integrations() -> None:
    mesh = SovereignRecoveryMesh()
    mesh.register("profiles", RecoveryProfile("profile", "subject"))
    snapshot = dashboard_snapshot(mesh)
    assert len(mesh.overview()["integrations"]) == 10
    assert mesh.health()["readiness"]
    assert mesh.metrics()["v10_recovery_profiles_total"] == 1
    assert len(DASHBOARD_SECTIONS) == 9
    assert snapshot["actions"] == ()
    assert mesh.audit()


def test_api_openapi_and_server_are_exactly_ten_get_only_routes() -> None:
    app = FakeApp()
    register_routes(app)
    assert len(GET_ROUTES) == 10
    assert {method for method, _ in app.routes.values()} == {"GET"}
    assert all(
        set(operations) == {"get"}
        for operations in openapi_contract()["paths"].values()
    )
    from server.api.app import create_app

    server = create_app()
    methods = {
        route.path: route.methods
        for route in server.routes
        if route.path.startswith("/v10/recovery/")
    }
    assert set(GET_ROUTES) == set(methods)
    assert all(value == {"GET"} for value in methods.values())


def test_forbidden_recovery_rollback_restore_and_mutation_absent() -> None:
    forbidden = (
        "execute",
        "rollback",
        "restore",
        "apply",
        "mutate",
        "write",
        "create",
        "update",
        "delete",
        "deploy",
    )
    assert not any(any(term in path for term in forbidden) for path in GET_ROUTES)
    mesh = SovereignRecoveryMesh()
    assert not any(
        hasattr(mesh, name)
        for name in (
            "execute",
            "recover",
            "rollback",
            "restore",
            "apply",
            "deploy",
        )
    )
    assert all(value is False for value in mesh.diagnostics().values())
    overview = mesh.overview()
    assert overview["recovery_execution"] == "disabled"
    assert overview["rollback_execution"] == "disabled"
    assert overview["snapshot_restore"] == "disabled"


def test_v6_v7_v8_v9_v10_regression_imports() -> None:
    import tkai.v7
    import tkai.v8
    import tkai.v9
    import tkai.v10

    assert all((tkai.v7, tkai.v8, tkai.v9, tkai.v10))
    assert SovereignRecoveryMesh().overview()["generations"] == (
        "v6",
        "v7",
        "v8",
        "v9",
        "v10",
    )
