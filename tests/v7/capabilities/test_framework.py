from __future__ import annotations

import importlib
from unittest.mock import Mock

import pytest

from tkai.v7.capabilities import (
    CapabilityDashboard,
    CapabilityLifecycle,
    CapabilityLoader,
    CapabilityModel,
    CapabilityRegistry,
    CapabilityStatus,
    CapabilityValidationError,
    Dependency,
    DependencyCycleError,
    HealthStatus,
    Interface,
    UpgradePath,
    compatible,
)
from tkai.v7.capabilities.api import register_capability_routes
from tkai.v7.capabilities.contracts import serialize
from tkai.v7.contracts import Version, VersionRange


def model(
    identifier: str, dependencies: tuple[Dependency, ...] = ()
) -> CapabilityModel:
    return CapabilityModel(
        capability_id=identifier,
        name=identifier.title(),
        description="Mock capability",
        owner="tests",
        version=Version(7),
        category="test",
        dependencies=dependencies,
        interfaces=(Interface("test.interface"),),
        permissions=frozenset({"capability.read"}),
        tags=frozenset({"mock"}),
        metadata={"token": "never-expose", "visible": "yes"},
        configuration={"api_key": "also-never-expose"},
        upgrade_paths=(UpgradePath(Version(6), Version(7)),),
    )


class Provider:
    def __init__(self, value: CapabilityModel) -> None:
        self.capability = value
        self.calls: list[str] = []

    def load(self) -> None:
        self.calls.append("load")

    def activate(self) -> None:
        self.calls.append("activate")

    def pause(self) -> None:
        self.calls.append("pause")

    def disable(self) -> None:
        self.calls.append("disable")


def test_all_required_packages_import() -> None:
    packages = (
        "registry",
        "contracts",
        "loader",
        "resolver",
        "validator",
        "catalog",
        "metadata",
        "versioning",
        "dependencies",
        "permissions",
        "health",
        "metrics",
        "audit",
        "events",
        "lifecycle",
        "extensions",
        "dashboard",
        "api",
    )
    for package in packages:
        assert importlib.import_module(f"tkai.v7.capabilities.{package}")


def test_registry_discovery_filtering_lookup_and_index() -> None:
    registry = CapabilityRegistry()
    registered = registry.register(model("test.read"))
    assert registered.status is CapabilityStatus.REGISTERED
    assert registry.get("test.read") == registered
    assert registry.lookup("test.read", VersionRange(Version(7), Version(7)))
    assert registry.discover(category="test", tags={"mock"}) == (registered,)
    assert registry.index("owner", "tests") == (registered,)
    with pytest.raises(ValueError):
        registry.register(model("test.read"))


def test_dependency_validation_graph_and_cycle_detection() -> None:
    registry = CapabilityRegistry()
    registry.register(model("base"))
    registry.register(model("child", (Dependency("base"),)))
    assert registry.graph().load_order("child") == ("base", "child")
    assert registry.graph().dependents("base") == ("child",)
    missing = CapabilityRegistry()
    missing.register(model("broken", (Dependency("absent"),)))
    with pytest.raises(CapabilityValidationError):
        missing.validate("broken", granted_permissions={"capability.read"})
    cyclic = CapabilityRegistry()
    cyclic.register(model("one", (Dependency("two"),)))
    cyclic.register(model("two", (Dependency("one"),)))
    with pytest.raises(DependencyCycleError):
        cyclic.graph().load_order()


def test_loader_lifecycle_metrics_health_and_audit() -> None:
    registry = CapabilityRegistry()
    descriptor = model("test.load")
    provider = Provider(descriptor)
    registry.register(descriptor, provider)
    loader = CapabilityLoader(registry)
    assert (
        loader.load("test.load", granted_permissions={"capability.read"}).status
        is CapabilityStatus.LOADED
    )
    assert loader.activate("test.load").status is CapabilityStatus.ACTIVE
    lifecycle = CapabilityLifecycle(registry)
    assert lifecycle.pause("test.load").status is CapabilityStatus.PAUSED
    assert loader.activate("test.load").status is CapabilityStatus.ACTIVE
    assert lifecycle.disable("test.load").status is CapabilityStatus.DISABLED
    assert provider.calls == ["load", "activate", "pause", "activate", "disable"]
    metrics = registry.metrics.get("test.load")
    assert metrics.load_count == 1
    assert metrics.activation_count == 2
    registry.health.register(
        "test.load", lambda: {"ready": True, "live": True, "token": "secret"}
    )
    health = registry.health.check("test.load")
    assert health.status is HealthStatus.HEALTHY
    assert health.diagnostics["token"] == "[REDACTED]"
    assert registry.audit.list("test.load")


def test_permission_validation_versioning_and_secret_safe_serialization() -> None:
    registry = CapabilityRegistry()
    registry.register(model("secure"))
    with pytest.raises(CapabilityValidationError, match="permissions not granted"):
        registry.validate("secure", granted_permissions=set())
    assert compatible(Version(7, 2), Version(7, 1))
    assert not compatible(Version(8), Version(7))
    payload = serialize(model("safe"))
    assert "configuration" not in payload
    assert payload["version"] == "7.0.0"


def test_dashboard_and_get_only_api_surface() -> None:
    registry = CapabilityRegistry()
    registry.register(model("view"))
    dashboard = CapabilityDashboard(registry).snapshot()
    assert set(dashboard) == {
        "catalog",
        "registry",
        "dependencies",
        "health",
        "metrics",
        "audit",
        "versions",
        "lifecycle",
    }
    app = Mock()
    register_capability_routes(app, registry)
    paths = [call.args[0] for call in app.add_api_route.call_args_list]
    assert paths == [
        "/v7/capabilities/catalog",
        "/v7/capabilities/registry",
        "/v7/capabilities/health",
        "/v7/capabilities/metrics",
        "/v7/capabilities/lifecycle",
        "/v7/capabilities/dependencies",
        "/v7/capabilities/versions",
        "/v7/capabilities/audit",
    ]
