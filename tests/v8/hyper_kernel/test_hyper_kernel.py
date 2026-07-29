"""Offline tests for the TKAI V8 Hyper Kernel."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from tkai.v8.api import GET_ROUTES, register_routes
from tkai.v8.contracts import (
    Dependency,
    Diagnostic,
    FrameworkKind,
    HealthStatus,
    RegistryRecord,
    Scope,
)
from tkai.v8.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v8.kernel import HyperKernel
from tkai.v8.registry import DuplicateRegistrationError, RegistryError
from tkai.v8.security import Principal, filter_secrets
from tkai.v8.services import DependencyGraph


class FakeApp:
    """Small FastAPI-compatible recorder that never opens a socket."""

    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def get(self, path: str, **kwargs: object):  # type: ignore[no-untyped-def]
        def decorator(handler: object) -> object:
            self.routes[path] = ("GET", handler)
            return handler

        return decorator


def test_kernel_identity_defaults_and_framework_registry() -> None:
    kernel = HyperKernel(metadata={"environment": "test"})

    assert kernel.ID == HyperKernel().ID
    assert kernel.VERSION == "8.0.0"
    assert kernel.overview()["execution"] == "disabled"
    assert set(kernel.framework_registry.supported_kinds()) == {
        kind.value for kind in FrameworkKind
    }
    assert len(kernel.framework_registry) == len(FrameworkKind)


def test_registry_isolation_discovery_and_immutability() -> None:
    kernel = HyperKernel(register_defaults=False)
    record = RegistryRecord(
        "example",
        "1.0.0",
        "capability",
        Scope("tenant-a", "workspace-a", "framework-a"),
        metadata={"owner": "platform"},
    )
    kernel.register("capabilities", record, actor="tester")

    assert kernel.capability_registry.discover(
        scope=Scope("tenant-a", "workspace-a", "*")
    ) == (record,)
    assert not kernel.capability_registry.discover(
        scope=Scope("tenant-b", "workspace-a", "*")
    )
    with pytest.raises(DuplicateRegistrationError):
        kernel.register("capabilities", record)
    with pytest.raises(TypeError):
        record.metadata["owner"] = "changed"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        record.kind = "service"  # type: ignore[misc]


def test_discovery_dependency_graph_and_diagnostics_are_reference_only() -> None:
    kernel = HyperKernel(register_defaults=False)
    kernel.register(
        "modules",
        RegistryRecord("storage", "1", "service", health=HealthStatus.HEALTHY),
    )
    kernel.register(
        "modules",
        RegistryRecord(
            "catalog",
            "1",
            "service",
            dependencies=(Dependency("storage"),),
            capabilities=frozenset({"catalog.read"}),
            health=HealthStatus.DEGRADED,
        ),
    )
    kernel.register(
        "modules",
        RegistryRecord(
            "broken",
            "1",
            "service",
            dependencies=(Dependency("missing"),),
        ),
    )

    assert kernel.discovery.services()[1].identifier == "catalog"
    assert kernel.dependency_graph()["catalog"] == ("storage",)
    assert DependencyGraph(kernel.registries.values()).resolve("catalog") == (
        "storage",
        "catalog",
    )
    diagnostics = kernel.diagnostics()
    assert diagnostics[0].code == "missing-dependency"
    assert kernel.health()["status"] == "degraded"


def test_compatibility_matrix_covers_v6_v7_and_existing_surfaces() -> None:
    kernel = HyperKernel()
    identifiers = set(kernel.compatibility_registry.identifiers())

    assert {
        "tkai-v6",
        "tkai-v7",
        "tiktok-modules",
        "openapi",
        "dashboard",
        "ai-studio",
    } <= identifiers


def test_security_rbac_isolation_and_secret_filtering() -> None:
    kernel = HyperKernel(metadata={"api_key": "hidden", "safe": "visible"})
    principal = Principal("reader", tenant="tenant-a", workspace="workspace-a")

    kernel.authorize_read(principal, Scope("tenant-a", "workspace-a"))
    with pytest.raises(PermissionError, match="tenant isolation"):
        kernel.authorize_read(principal, Scope("tenant-b", "workspace-a"))
    with pytest.raises(PermissionError, match="workspace isolation"):
        kernel.authorize_read(principal, Scope("tenant-a", "workspace-b"))
    assert kernel.metadata == {"api_key": "[REDACTED]", "safe": "visible"}
    assert filter_secrets({"nested": {"password": "hidden"}}) == {
        "nested": {"password": "[REDACTED]"}
    }


def test_observability_health_metrics_diagnostics_and_audit() -> None:
    kernel = HyperKernel(register_defaults=False)
    kernel.add_diagnostic(Diagnostic("test", "offline diagnostic"))
    kernel.register(
        "runtime",
        RegistryRecord(
            "runtime-reference", "1", "runtime", health=HealthStatus.HEALTHY
        ),
        actor="operator",
    )
    kernel.observability.log("info", "safe", {"token": "hidden"})
    kernel.observability.trace("read", "trace-1", {"secret": "hidden"})

    assert kernel.health()["status"] == "healthy"
    assert kernel.metrics()["registries"]["runtime"] == 1  # type: ignore[index]
    assert kernel.diagnostics()[0].code == "test"
    assert kernel.audit()[-1]["actor"] == "operator"
    assert kernel.observability.logs()[0]["metadata"] == {"token": "[REDACTED]"}
    assert kernel.observability.traces()[0].metadata == {"secret": "[REDACTED]"}


def test_dashboard_contains_all_required_sections() -> None:
    snapshot = dashboard_snapshot(HyperKernel())

    assert snapshot["sections"] == DASHBOARD_SECTIONS
    assert set(DASHBOARD_SECTIONS) == {
        "Kernel Overview",
        "Framework Registry",
        "Capabilities",
        "Runtime",
        "Health",
        "Metrics",
        "Diagnostics",
        "Audit",
    }


def test_api_is_get_only_and_transport_neutral() -> None:
    app = FakeApp()
    kernel = register_routes(app, HyperKernel())

    assert set(app.routes) == set(GET_ROUTES)
    assert {method for method, _ in app.routes.values()} == {"GET"}
    handler = app.routes["/v8/kernel"][1]
    assert callable(handler)
    assert handler()["kernel_id"] == kernel.ID  # type: ignore[operator]


def test_invalid_framework_and_unknown_registry_are_rejected() -> None:
    kernel = HyperKernel(register_defaults=False)
    with pytest.raises(RegistryError, match="unsupported framework"):
        kernel.framework_registry.register(
            RegistryRecord("unknown", "1", "not-a-framework")
        )
    with pytest.raises(ValueError, match="unknown registry"):
        kernel.register("executors", RegistryRecord("x", "1", "service"))
