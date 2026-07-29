from dataclasses import replace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tkai.v7.extension_framework import (
    Compatibility,
    Dependency,
    ExtensionFramework,
    ExtensionFrameworkError,
    ExtensionManifest,
    HealthMetadata,
    IsolationError,
    Lifecycle,
    LifecycleError,
    PackageMetadata,
    PluginManifest,
    SandboxMetadata,
    Scope,
    SignatureMetadata,
    ValidationStatus,
    VerificationStatus,
    serialize,
    version_satisfies,
)
from tkai.v7.extension_framework.api import (
    EXTENSION_ENDPOINTS,
    register_extension_framework_routes,
)
from tkai.v7.extension_framework.dashboard import (
    DASHBOARD_SECTIONS,
    ExtensionDashboard,
)


def extension(
    extension_id: str,
    scope: Scope,
    *,
    dependencies: tuple[Dependency, ...] = (),
    plugin_ids: tuple[str, ...] = (),
    permissions: frozenset[str] = frozenset({"catalog:read"}),
) -> ExtensionManifest:
    return ExtensionManifest(
        extension_id,
        extension_id.title(),
        "internal metadata extension",
        "internal",
        "platform",
        "1.2.0",
        scope,
        plugin_ids=plugin_ids,
        dependencies=dependencies,
        permissions=permissions,
        capabilities=frozenset({f"{extension_id}:read"}),
        compatibility=Compatibility(
            required_capabilities=frozenset({"extensions"}),
            required_interfaces={"catalog": "^1.0.0"},
            migration_metadata={"from": "v6", "automatic": False},
        ),
        health=HealthMetadata("healthy", {"manifest": "pass"}),
    )


def framework() -> tuple[ExtensionFramework, Scope]:
    scope = Scope("tenant-a", "workspace-a")
    item = ExtensionFramework(
        platform_capabilities={"extensions"},
        platform_interfaces={"catalog": "1.4.0"},
    )
    item.register_extension(extension("base", scope))
    item.register_extension(
        extension(
            "reporting",
            scope,
            dependencies=(Dependency("base", "^1.0.0"),),
            plugin_ids=("summary",),
        )
    )
    item.register_plugin(
        PluginManifest(
            "summary",
            "reporting",
            "Summary",
            "read-only summaries",
            "reporting",
            "platform",
            "1.0.0",
            scope,
            permissions=frozenset({"catalog:read"}),
        )
    )
    return item, scope


def test_static_discovery_registry_and_indexes() -> None:
    scope = Scope("tenant-a", "workspace-a")
    item = ExtensionFramework()
    discovered = item.discover_static((extension("search", scope),))
    assert discovered[0].lifecycle is Lifecycle.DISCOVERED
    assert item.registry.by_capability("search:read", scope) == discovered
    assert item.lookup_metadata("metadata", scope) == discovered


def test_plugin_registration_and_scope_isolation() -> None:
    item, scope = framework()
    assert item.registry.plugins_for(scope)[0].extension_id == "reporting"
    other_scope = Scope("tenant-b", "workspace-a")
    with pytest.raises(IsolationError):
        item.register_plugin(
            PluginManifest(
                "other",
                "reporting",
                "Other",
                "bad scope",
                "test",
                "test",
                "1.0.0",
                other_scope,
            )
        )


def test_validation_dependencies_and_compatibility() -> None:
    item, _ = framework()
    assert item.validate("reporting").status is ValidationStatus.VALID
    resolution = item.resolve_dependencies(
        item.registry.extensions.get("reporting", ExtensionManifest)
    )
    assert resolution.satisfied is True
    assert resolution.ordered_extension_ids == ("base",)
    result = item.check_compatibility("reporting")
    assert result.compatible is True
    assert result.migration_metadata["automatic"] is False


def test_missing_dependency_permission_and_interface_failures() -> None:
    scope = Scope("tenant-a", "workspace-a")
    item = ExtensionFramework()
    bad = extension(
        "bad",
        scope,
        dependencies=(Dependency("missing", ">=1.0.0"),),
        permissions=frozenset({"network:write"}),
    )
    item.register_extension(bad)
    result = item.validate("bad")
    assert result.status is ValidationStatus.INVALID
    assert {issue.code for issue in result.issues} == {"dependency", "permission"}
    assert item.check_compatibility("bad").compatible is False
    assert item.metric_values["v7_extension_security_rejections_total"] == 1


def test_package_signature_and_sandbox_are_metadata_only() -> None:
    scope = Scope("tenant-a", "workspace-a")
    package = PackageMetadata(
        "reporting-package",
        "1.0.0",
        "manifest://reporting",
        {"manifest.json": "a" * 64},
    )
    signature = SignatureMetadata(
        "reporting-signature",
        "sha256:abc",
        "ed25519",
        VerificationStatus.VERIFIED,
        {"authority": "internal"},
        verified_locally=True,
    )
    item = ExtensionFramework()
    item.register_extension(
        replace(extension("packaged", scope), package=package, signature=signature)
    )
    assert item.projection("packages", scope)[0]["installable"] is False
    assert item.projection("signatures", scope)[0]["remote_verification"] is False
    with pytest.raises(ValueError):
        SandboxMetadata(executable_runtime=True)
    with pytest.raises(ValueError):
        replace(package, installable=True)
    with pytest.raises(ValueError):
        replace(signature, remote_verification=True)


def test_lifecycle_health_metrics_audit_and_tracing() -> None:
    item, scope = framework()
    item.transition_extension("reporting", Lifecycle.VALIDATED, scope)
    item.transition_extension("reporting", Lifecycle.COMPATIBLE, scope)
    available = item.transition_extension("reporting", Lifecycle.AVAILABLE, scope)
    assert available.lifecycle is Lifecycle.AVAILABLE
    assert item.projection("health", scope)["code_execution"] is False
    assert item.projection("metrics", scope)["v7_extensions_registered_total"] == 2
    assert item.projection("audit", scope)
    assert item.traces[-1]["hook"] == "v7.extension_framework"
    with pytest.raises(LifecycleError):
        item.transition_extension("reporting", Lifecycle.REGISTERED, scope)


def test_dashboard_has_all_required_sections() -> None:
    item, scope = framework()
    snapshot = ExtensionDashboard(item).snapshot(scope)
    assert set(snapshot) == set(DASHBOARD_SECTIONS)
    assert snapshot["plugins"][0]["plugin_id"] == "summary"


def test_get_only_api_and_openapi_contract() -> None:
    app = FastAPI()
    item, _ = framework()
    register_extension_framework_routes(app, item)
    client = TestClient(app)
    params = {
        "tenant": "tenant-a",
        "workspace": "workspace-a",
        "namespace": "extensions",
    }
    for endpoint in EXTENSION_ENDPOINTS:
        path = f"/v7/extensions/{endpoint}"
        assert client.get(path, params=params).status_code == 200
        assert client.post(path, params=params).status_code == 405
    paths = app.openapi()["paths"]
    assert all(
        set(paths[f"/v7/extensions/{endpoint}"]) == {"get"}
        for endpoint in EXTENSION_ENDPOINTS
    )


def test_secret_filtering_and_no_executable_operations() -> None:
    safe = serialize(
        {"token": "do-not-leak", "nested": {"api_key": "also-secret"}, "name": "ok"}
    )
    assert safe == {
        "token": "[REDACTED]",
        "nested": {"api_key": "[REDACTED]"},
        "name": "ok",
    }
    item = ExtensionFramework()
    for forbidden in ("download", "install", "execute", "load_module", "verify_remote"):
        assert not hasattr(item, forbidden)


def test_semantic_version_compatibility() -> None:
    assert version_satisfies("1.4.2", "^1.0.0")
    assert version_satisfies("1.4.2", ">=1.2.0,<2.0.0")
    assert version_satisfies("1.4.2", "~1.4.0")
    assert not version_satisfies("2.0.0", "^1.0.0")
    assert not version_satisfies("1.0.0", "not-a-constraint")


def test_v6_plugin_and_tkai_imports_remain_available() -> None:
    import tkai
    import tkai.plugins

    assert tkai is not None
    assert tkai.plugins is not None
    assert not hasattr(ExtensionFrameworkError, "tiktok_behavior")
