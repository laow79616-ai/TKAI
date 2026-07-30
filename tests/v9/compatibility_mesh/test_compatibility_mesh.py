from dataclasses import FrozenInstanceError

import pytest

from tkai.v9.compatibility_mesh import (
    AdaptiveCompatibilityMesh,
    Assessment,
    CompatibilityRecord,
    CompatibilityScope,
    Matrix,
    Profile,
    Recommendation,
    Reference,
)
from tkai.v9.compatibility_mesh.api import GET_ROUTES, openapi_contract, route_handlers
from tkai.v9.compatibility_mesh.dashboard import (
    DASHBOARD_SECTIONS,
    dashboard_snapshot,
)
from tkai.v9.compatibility_mesh.security import authorize


def ref(
    identifier: str = "ref-1",
    generation: str = "v9",
    framework: str = "v9_components",
) -> Reference:
    return Reference(identifier, generation=generation, framework=framework)


def scope() -> CompatibilityScope:
    return CompatibilityScope("tenant-a", "workspace-a", "compat-a", "profile-a")


def test_profile_is_immutable_and_non_executable() -> None:
    profile = Profile(
        "p",
        "Compatibility",
        "Reference-only",
        "9.0.0",
        "owner",
        "compat-a",
        ref("tenant"),
        ref("workspace"),
        scope=scope(),
        source_generation="v6",
    )
    assert not profile.execution_authorized
    with pytest.raises(FrozenInstanceError):
        profile.owner = "other"  # type: ignore[misc]


def test_federation_supports_v6_v7_v8_v9_and_is_local_read_only() -> None:
    mesh = AdaptiveCompatibilityMesh(maximum_sources=4)
    sources = tuple(
        ref(f"{generation}-ref", generation, f"{generation}_frameworks")
        for generation in ("v6", "v7", "v8")
    ) + (ref("v9-ref"),)
    assert tuple(item.generation for item in mesh.federate(sources)) == (
        "v6",
        "v7",
        "v8",
        "v9",
    )
    assert not mesh.federation.mutates_upstream()
    with pytest.raises(ValueError, match="bounded"):
        AdaptiveCompatibilityMesh(maximum_sources=1).federate(sources)
    with pytest.raises(ValueError, match="allowlisted"):
        mesh.federate((ref("unknown", framework="unknown"),))
    with pytest.raises(ValueError, match="network"):
        mesh.federate(
            (Reference("remote", framework="v8_frameworks", metadata={"remote": True}),)
        )


def test_records_assessments_matrices_and_recommendations_are_advisory() -> None:
    mesh = AdaptiveCompatibilityMesh()
    record = CompatibilityRecord(
        "compat-1",
        "schema",
        ref("v8-schema", "v8", "v8_frameworks"),
        ref("v9-schema"),
        status="compatible",
        scope=scope(),
    )
    assessment = Assessment(
        "assessment-1",
        "schema",
        ref("v8-schema", "v8", "v8_frameworks"),
        ref("v9-schema"),
        "compatible",
        1.0,
        {"shape": 1.0},
        {"shape": 1.0},
        explanation_summary="Shapes are compatible",
        scope=scope(),
    )
    matrix = Matrix("matrix-1", "v8", "v9", (record,), scope=scope())
    recommendation = Recommendation(
        "recommendation-1", "review", ref(), "Manual review", scope=scope()
    )
    mesh.register("compatibility_records", record)
    mesh.register("assessments", assessment)
    mesh.register("matrices", matrix)
    mesh.register("recommendations", recommendation)
    snapshot = mesh.snapshot()
    assert snapshot["compatibility"][0]["executable"] is False
    assert recommendation.advisory and not recommendation.executable
    assert not record.mutates_configuration
    assert not record.mutates_schema
    assert not record.mutates_storage


def test_all_prohibited_operations_are_disabled() -> None:
    mesh = AdaptiveCompatibilityMesh()
    checks = (
        mesh.executes_tiktok_actions,
        mesh.mutates_runtime_state,
        mesh.executes_migration,
        mesh.executes_upgrade,
        mesh.executes_rollback,
        mesh.applies_configuration,
        mesh.mutates_schema,
        mesh.mutates_storage,
        mesh.installs_plugins,
        mesh.executes_deployment,
        mesh.approves_execution,
    )
    assert not any(check() for check in checks)
    overview = mesh.overview()
    prohibited = (
        "execution",
        "runtime_mutation",
        "automatic_migration",
        "automatic_upgrade",
        "rollback_execution",
        "configuration_apply",
        "schema_mutation",
        "storage_mutation",
        "plugin_installation",
        "deployment_execution",
        "tiktok_actions",
    )
    assert all(overview[item] == "disabled" for item in prohibited)
    assert mesh.compatibility()["generations"] == ("v6", "v7", "v8", "v9")


def test_security_health_dashboard_and_get_only_api() -> None:
    actual = scope()
    assert authorize("read", actual, actual)
    assert not authorize("execute", actual, actual)
    with pytest.raises(ValueError, match="secret"):
        AdaptiveCompatibilityMesh(metadata={"nested": {"session": "no"}})
    mesh = AdaptiveCompatibilityMesh()
    assert mesh.health()["status"] == "healthy"
    assert "v9_compatibility_mesh_profiles_total" in mesh.metrics()
    assert dashboard_snapshot(mesh)["sections"] == DASHBOARD_SECTIONS
    assert set(route_handlers(mesh)) == set(GET_ROUTES)
    assert all(set(value) == {"get"} for value in openapi_contract()["paths"].values())
    prohibited_routes = ("execute", "apply", "install", "mutate")
    assert not any(
        any(term in route for term in prohibited_routes) for route in GET_ROUTES
    )


def test_server_integration_registers_get_only_routes() -> None:
    from server.api.app import create_app

    app = create_app()
    methods = {
        route.path: route.methods
        for route in app.routes
        if route.path.startswith("/v9/compatibility/")
    }
    assert set(GET_ROUTES) <= set(methods)
    assert all(value == {"GET"} for value in methods.values())
