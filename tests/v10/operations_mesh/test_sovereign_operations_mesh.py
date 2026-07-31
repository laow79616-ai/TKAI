"""Offline mock-only tests for the V10 Sovereign Operations Mesh."""
# ruff: noqa: E501

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from tkai.v10.contracts import Scope
from tkai.v10.operations_mesh import (
    AssessmentType,
    Availability,
    AvailabilityStatus,
    Capacity,
    Maintenance,
    OperationalAssessment,
    OperationalContext,
    OperationalStatus,
    OperationReference,
    OperationsProfile,
    OperationsValidation,
    Readiness,
    SovereignOperationsMesh,
)
from tkai.v10.operations_mesh.api import GET_ROUTES, openapi_contract, register_routes
from tkai.v10.operations_mesh.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v10.operations_mesh.security import authorize_metadata_read


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def add_api_route(
        self, path: str, handler: object, *, methods: list[str], **_: object
    ) -> None:
        self.routes[path] = (methods[0], handler)


def test_repository_structure_profile_and_generation_compatibility() -> None:
    root = Path(__file__).resolve().parents[3]
    assert root.resolve() == Path(r"C:\Users\laow7\Documents\TKAI").resolve()
    required = set(
        """profiles registry contexts operations readiness maintenance capacity availability
        dependencies assessments governance compatibility integrity trust planning decision
        reasoning knowledge validation diagnostics health metrics audit security events
        contracts interfaces lifecycle dashboard api""".split()
    )
    package = root / "src/tkai/v10/operations_mesh"
    assert required <= {path.name for path in package.iterdir() if path.is_dir()}
    profile = OperationsProfile("profile", "subject", safe_metadata={"label": "safe"})
    with pytest.raises(FrozenInstanceError):
        profile.health = "bad"  # type: ignore[misc]
    mesh = SovereignOperationsMesh()
    mesh.register("profiles", profile)
    assert {item.generation for item in mesh.discover("compatibility")} == {
        "v6",
        "v7",
        "v8",
        "v9",
        "v10",
    }


def test_contexts_and_operational_states_are_metadata_only() -> None:
    mesh = SovereignOperationsMesh()
    context = OperationalContext("context", "subject", "bounded")
    operation = OperationReference(
        "operation", "subject", OperationalStatus.CONDITIONALLY_READY, ("context",)
    )
    mesh.register("contexts", context)
    mesh.register("operations", operation)
    assert len(OperationalStatus) == 6
    assert context.metadata_only
    assert not operation.executable
    assert mesh.discover("operations") == (operation,)


def test_readiness_and_maintenance_never_execute_or_schedule() -> None:
    mesh = SovereignOperationsMesh()
    readiness = Readiness("ready", "subject", OperationalStatus.READY)
    maintenance = Maintenance("maintenance", "subject")
    mesh.register("readiness", readiness)
    mesh.register("maintenance", maintenance)
    assert readiness.metadata_only
    assert maintenance.metadata_only
    assert not maintenance.executable
    assert not maintenance.schedulable
    assert not any(
        hasattr(mesh, name) for name in ("execute", "schedule", "start", "stop")
    )


def test_capacity_is_reference_only_and_never_allocates() -> None:
    capacity = Capacity(
        "capacity",
        "subject",
        "capacity:reference",
        "utilization:reference",
        limits={"workers": 10},
        thresholds={"warning": 0.8},
        warnings=("estimate only",),
    )
    mesh = SovereignOperationsMesh()
    mesh.register("capacity", capacity)
    assert capacity.reference_only
    assert not capacity.allocates_resources
    assert capacity.warnings == ("estimate only",)


def test_availability_is_metadata_only_and_never_repairs_health() -> None:
    availability = Availability(
        "availability", "subject", AvailabilityStatus.LIMITED, ("evidence",)
    )
    mesh = SovereignOperationsMesh()
    mesh.register("availability", availability)
    assert len(AvailabilityStatus) == 4
    assert availability.metadata_only
    assert not availability.repairs_health


def test_all_ten_operational_assessment_types_are_supported() -> None:
    mesh = SovereignOperationsMesh()
    for index, assessment_type in enumerate(AssessmentType):
        mesh.register(
            "assessments",
            OperationalAssessment(
                f"assessment-{index}",
                "subject",
                assessment_type,
                deployment_reference="deployment:reference",
                runtime_reference="runtime:reference",
            ),
        )
    assert len(AssessmentType) == 10
    assert len(mesh.discover("assessments")) == 10


def test_validation_bounds_rbac_isolation_and_secret_filtering() -> None:
    mesh = SovereignOperationsMesh(per_registry_limit=5)
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
            OperationsProfile(
                "bad", "subject", safe_metadata={"chain_of_thought": "secret"}
            ),
        )
    assert mesh.serialize({"api_key": "secret"}) == {"api_key": "[REDACTED]"}
    with pytest.raises(ValueError, match="between 0 and 100"):
        mesh.discover("profiles", limit=101)
    validation = OperationsValidation("validation", "subject", "valid")
    mesh.register("validation", validation)
    assert validation.metadata_only


def test_integrations_dashboard_health_metrics_and_audit() -> None:
    mesh = SovereignOperationsMesh()
    mesh.register("profiles", OperationsProfile("profile", "subject"))
    snapshot = dashboard_snapshot(mesh)
    assert len(mesh.overview()["integrations"]) == 9
    assert mesh.health()["readiness"]
    assert mesh.metrics()["v10_operations_profiles_total"] == 1
    assert len(mesh.metrics()) == 11
    assert len(DASHBOARD_SECTIONS) == 12
    assert snapshot["actions"] == ()
    assert mesh.audit()


def test_api_and_openapi_are_exactly_ten_get_only_routes() -> None:
    app = FakeApp()
    register_routes(app)
    assert len(GET_ROUTES) == 10
    assert {method for method, _ in app.routes.values()} == {"GET"}
    assert all(
        set(operations) == {"get"}
        for operations in openapi_contract()["paths"].values()
    )
    assert set(GET_ROUTES) == {
        f"/v10/operations/{name}"
        for name in (
            "profiles",
            "contexts",
            "readiness",
            "maintenance",
            "capacity",
            "availability",
            "assessments",
            "validation",
            "health",
            "metrics",
        )
    }


def test_server_integration_registers_operations_routes_get_only() -> None:
    from server.api.app import create_app

    app = create_app()
    methods = {
        route.path: route.methods
        for route in app.routes
        if route.path.startswith("/v10/operations/")
    }
    assert set(GET_ROUTES) == set(methods)
    assert all(value == {"GET"} for value in methods.values())


def test_forbidden_execution_scheduler_and_service_control_endpoints_absent() -> None:
    forbidden = (
        "execute",
        "apply",
        "schedule",
        "scheduler",
        "allocate",
        "mutate",
        "write",
        "create",
        "update",
        "delete",
        "start",
        "stop",
        "restart",
        "deploy",
    )
    assert not any(any(term in path for term in forbidden) for path in GET_ROUTES)
    diagnostics = SovereignOperationsMesh().diagnostics()
    assert all(value is False for value in diagnostics.values())
    assert not diagnostics["service_start"]
    assert not diagnostics["service_stop"]
    assert not diagnostics["service_restart"]


def test_v6_v7_v8_v9_v10_regression_imports_and_safety_contract() -> None:
    import tkai.v7
    import tkai.v8
    import tkai.v9
    import tkai.v10

    assert all((tkai.v7, tkai.v8, tkai.v9, tkai.v10))
    overview = SovereignOperationsMesh().overview()
    assert overview["generations"] == ("v6", "v7", "v8", "v9", "v10")
    assert overview["execution"] == "disabled"
    assert overview["scheduler"] == "disconnected"
    assert overview["service_control"] == "disabled"
    assert overview["resource_allocation"] is False
    assert overview["runtime_mutation"] is False
