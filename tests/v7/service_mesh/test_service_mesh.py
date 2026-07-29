from __future__ import annotations

import importlib
from unittest.mock import Mock

import pytest

from tkai.v7.contracts import Version, VersionRange
from tkai.v7.security import AccessController, Principal
from tkai.v7.service_mesh import (
    DependencyCycleError,
    HealthStatus,
    RouteNotFoundError,
    ServiceDependency,
    ServiceEndpoint,
    ServiceInterface,
    ServiceLifecycle,
    ServiceMeshDashboard,
    ServiceModel,
    ServiceRegistry,
    ServiceRouter,
    ServiceSecurity,
    ServiceStatus,
    ServiceValidationError,
)
from tkai.v7.service_mesh.api import register_service_mesh_routes
from tkai.v7.service_mesh.logging import structured_event
from tkai.v7.service_mesh.tracing import TracingHooks


def service(
    identifier: str,
    *,
    priority: int = 100,
    dependencies: tuple[ServiceDependency, ...] = (),
    interface: str = "test.read",
) -> ServiceModel:
    return ServiceModel(
        service_id=identifier,
        name=identifier.title(),
        description="Mock internal service",
        version=Version(7),
        owner="tests",
        category="test",
        dependencies=dependencies,
        interfaces=(ServiceInterface(interface),),
        endpoints=(
            ServiceEndpoint(interface, f"service://{identifier}/read", priority),
        ),
        metadata={"token": "hidden", "visible": "yes"},
        required_capabilities=frozenset({"service.read"}),
    )


class Provider:
    def __init__(self, model: ServiceModel) -> None:
        self.service = model
        self.calls: list[str] = []

    def start(self) -> None:
        self.calls.append("start")

    def pause(self) -> None:
        self.calls.append("pause")

    def stop(self) -> None:
        self.calls.append("stop")


def running(
    registry: ServiceRegistry, model: ServiceModel
) -> tuple[Provider, ServiceModel]:
    provider = Provider(model)
    registry.register(model, provider)
    started = ServiceLifecycle(registry).start(
        model.service_id, granted_capabilities={"service.read"}
    )
    registry.health.heartbeat(model.service_id)
    return provider, started


def test_all_required_packages_import() -> None:
    packages = (
        "registry",
        "services",
        "discovery",
        "routing",
        "contracts",
        "interfaces",
        "resolver",
        "balancing",
        "health",
        "heartbeat",
        "metrics",
        "tracing",
        "logging",
        "audit",
        "security",
        "events",
        "lifecycle",
        "extensions",
        "dashboard",
        "api",
    )
    for package in packages:
        assert importlib.import_module(f"tkai.v7.service_mesh.{package}")


def test_registry_discovery_lookup_metadata_index_and_secret_filtering() -> None:
    registry = ServiceRegistry()
    registered = registry.register(service("catalog"))
    assert registry.get("catalog") == registered
    assert registry.list() == (registered,)
    assert registry.discover(category="test", interface="test.read") == (registered,)
    assert registry.index("owner", "tests") == (registered,)
    assert registered.metadata == {"token": "[REDACTED]", "visible": "yes"}
    with pytest.raises(ValueError):
        registry.register(service("catalog"))


def test_dependency_validation_versions_interfaces_graph_and_cycle() -> None:
    registry = ServiceRegistry()
    registry.register(service("base"))
    dependency = ServiceDependency(
        "base",
        VersionRange(Version(7), Version(7, 99, 99)),
        interface="test.read",
    )
    registry.register(service("child", dependencies=(dependency,)))
    assert registry.graph().resolve("child") == ("base", "child")
    assert registry.graph().dependents("base") == ("child",)

    broken = ServiceRegistry()
    broken.register(service("broken", dependencies=(ServiceDependency("absent"),)))
    with pytest.raises(ServiceValidationError, match="missing dependency"):
        broken.validate("broken", granted_capabilities={"service.read"})

    cyclic = ServiceRegistry()
    cyclic.register(service("one", dependencies=(ServiceDependency("two"),)))
    cyclic.register(service("two", dependencies=(ServiceDependency("one"),)))
    with pytest.raises(DependencyCycleError):
        cyclic.graph().resolve()


def test_lifecycle_health_heartbeat_diagnostics_metrics_and_audit() -> None:
    registry = ServiceRegistry()
    provider, started = running(registry, service("lifecycle"))
    assert started.status is ServiceStatus.RUNNING
    lifecycle = ServiceLifecycle(registry)
    assert lifecycle.pause("lifecycle").status is ServiceStatus.PAUSED
    assert lifecycle.resume("lifecycle").status is ServiceStatus.RUNNING
    assert lifecycle.stop("lifecycle").status is ServiceStatus.STOPPED
    assert lifecycle.retire("lifecycle").status is ServiceStatus.RETIRED
    assert provider.calls == ["start", "pause", "stop"]

    registry.health.register(
        "lifecycle",
        lambda: {"live": True, "ready": True, "password": "hidden"},
    )
    health = registry.health.check("lifecycle")
    assert health.status is HealthStatus.HEALTHY
    assert health.available
    assert health.diagnostics["password"] == "[REDACTED]"
    assert registry.audit.list("lifecycle")


def test_deterministic_priority_fallback_and_health_aware_reference_routing() -> None:
    registry = ServiceRegistry()
    running(registry, service("secondary", priority=20))
    running(registry, service("primary", priority=10))
    router = ServiceRouter(registry)
    assert router.route("test.read") == "service://primary/read"
    assert router.table()["test.read"][0]["service_id"] == "primary"
    assert registry.metrics.get("primary").route_count == 1

    registry.health.heartbeat("primary", ready=False)
    assert router.route("test.read") == "service://secondary/read"
    with pytest.raises(RouteNotFoundError):
        router.route("missing")
    assert router.route("missing", fallback=("test.read",)).startswith("service://")


def test_security_logging_tracing_audit_and_isolation() -> None:
    access = AccessController({"operator": {"service.read"}})
    security = ServiceSecurity(access)
    principal = Principal("test-user", frozenset({"operator"}))
    security.grant_services("catalog", {"catalog"})
    security.require_access(principal, "service.read", "catalog")
    with pytest.raises(PermissionError):
        security.require_service("catalog", "other")

    assert structured_event(
        "diagnostic", "catalog", {"api_key": "hidden"}
    )["fields"] == {"api_key": "[REDACTED]"}
    hook = Mock()
    tracing = TracingHooks()
    tracing.register(hook)
    tracing.emit("route", {"service_id": "catalog"})
    hook.assert_called_once()


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[object, tuple[str, ...]]] = {}

    def add_api_route(
        self,
        path: str,
        handler: object,
        *,
        methods: list[str],
        tags: list[str],
    ) -> None:
        assert tags == ["V7 Service Mesh"]
        self.routes[path] = (handler, tuple(methods))


def test_get_only_api_openapi_shape_and_dashboard_sections() -> None:
    registry = ServiceRegistry()
    running(registry, service("api"))
    app = FakeApp()
    register_service_mesh_routes(app, registry)
    expected = {
        f"/v7/services/{resource}"
        for resource in (
            "catalog",
            "registry",
            "routing",
            "health",
            "metrics",
            "lifecycle",
            "dependencies",
        )
    }
    assert set(app.routes) == expected
    assert all(methods == ("GET",) for _, methods in app.routes.values())
    for handler, _ in app.routes.values():
        assert callable(handler)
        assert handler()

    dashboard = ServiceMeshDashboard(registry).snapshot()
    assert set(dashboard) == {
        "catalog",
        "registry",
        "dependencies",
        "routing",
        "health",
        "metrics",
        "lifecycle",
        "audit",
    }


def test_v6_imports_and_tiktok_modules_remain_untouched() -> None:
    assert importlib.import_module("tkai.v7.capabilities")
    assert importlib.import_module("tiktok")
