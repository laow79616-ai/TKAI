from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest

from tiktok.runtime_manager import (
    HealthState,
    ManagedService,
    RestartMode,
    RestartPolicy,
    RuntimeInstance,
    RuntimeProcess,
    RuntimeScope,
    RuntimeStatus,
    RuntimeWorker,
    ServiceStatus,
    TikTokRuntimeManager,
)
from tiktok.runtime_manager.api import ROUTES, register_runtime_manager_routes
from tiktok.runtime_manager.metrics import METRIC_NAMES
from tiktok.runtime_manager.models import utcnow


def scope(workspace: str = "local") -> RuntimeScope:
    return RuntimeScope(
        "default",
        workspace,
        "operator",
        frozenset({"tiktok:runtime:admin"}),
    )


def manager(ports: dict[str, Any] | None = None) -> TikTokRuntimeManager:
    return TikTokRuntimeManager(
        RuntimeInstance("runtime-1", "Local Runtime", "local", "owner", "5.0"),
        ports,
    )


def service(
    service_id: str, dependencies: frozenset[str] = frozenset(), **kwargs: Any
) -> ManagedService:
    return ManagedService(
        service_id,
        service_id.replace("_", " ").title(),
        "default",
        "local",
        "5.0",
        dependencies=dependencies,
        **kwargs,
    )


def test_lifecycle_startup_shutdown_dependency_order_and_cleanup() -> None:
    calls: list[str] = []

    class Port:
        def validate(self, item: ManagedService, request: RuntimeScope) -> None:
            calls.append(f"validate:{item.id}")

        def start(self, item: ManagedService, request: RuntimeScope) -> None:
            calls.append(f"start:{item.id}")

        def health(self, item: ManagedService, request: RuntimeScope) -> bool:
            return True

        def drain(self, item: ManagedService, request: RuntimeScope) -> None:
            calls.append(f"drain:{item.id}")

        def stop(self, item: ManagedService, request: RuntimeScope) -> None:
            calls.append(f"stop:{item.id}")

        def cleanup(self, item: ManagedService, request: RuntimeScope) -> None:
            calls.append(f"cleanup:{item.id}")

    runtime = manager({"backend": Port(), "dashboard": Port()})
    runtime.register_service(service("backend"), scope())
    runtime.register_service(service("dashboard", frozenset({"backend"})), scope())
    runtime.start(scope())
    assert runtime.runtime.status is RuntimeStatus.RUNNING
    assert calls.index("start:backend") < calls.index("start:dashboard")
    runtime.register_process(
        RuntimeProcess("p1", "backend", "default", "local", "pid://1"), scope()
    )
    runtime.register_worker(RuntimeWorker("w1", "backend", "default", "local"), scope())
    runtime.stop(scope())
    assert runtime.runtime.status is RuntimeStatus.STOPPED
    assert calls.index("stop:dashboard") < calls.index("stop:backend")
    assert not runtime.processes and not runtime.workers


def test_startup_rollback_cycle_validation_and_bounded_coordination() -> None:
    class FailingPort:
        def validate(self, item: ManagedService, request: RuntimeScope) -> None:
            return None

        def start(self, item: ManagedService, request: RuntimeScope) -> None:
            raise RuntimeError("offline failure")

        def health(self, item: ManagedService, request: RuntimeScope) -> bool:
            return False

        def drain(self, item: ManagedService, request: RuntimeScope) -> None:
            return None

        def stop(self, item: ManagedService, request: RuntimeScope) -> None:
            return None

        def cleanup(self, item: ManagedService, request: RuntimeScope) -> None:
            return None

    runtime = manager({"dashboard": FailingPort()})
    runtime.register_service(service("backend"), scope())
    runtime.register_service(service("dashboard", frozenset({"backend"})), scope())
    with pytest.raises(RuntimeError):
        runtime.start(scope())
    assert runtime.services["backend"].status is ServiceStatus.STOPPED
    assert runtime.runtime.status is RuntimeStatus.RECOVERING
    runtime._locked = True
    with pytest.raises(RuntimeError, match="already active"):
        runtime.stop(scope())


def test_registry_rbac_isolation_health_supervision_and_no_secrets() -> None:
    runtime = manager()
    runtime.register_service(service("backend"), scope())
    with pytest.raises(PermissionError):
        runtime.register_service(service("other"), scope("other"))
    with pytest.raises(ValueError):
        runtime.register_service(
            service("secret", metadata={"token": "plaintext"}), scope()
        )
    runtime.start(scope())
    runtime.services["backend"].heartbeat_at = utcnow() - timedelta(seconds=90)
    assert runtime.supervise(scope()) == ["backend"]
    assert runtime.services["backend"].health is HealthState.UNHEALTHY


def test_recovery_limits_approval_and_restriction_stop() -> None:
    runtime = manager()
    runtime.register_service(
        service(
            "backend",
            restart_policy=RestartPolicy(
                RestartMode.MANUAL_APPROVAL,
                maximum_attempts=1,
                approval_required=True,
            ),
        ),
        scope(),
    )
    runtime.start(scope())
    runtime.heartbeat("backend", False, 0.2, scope())
    with pytest.raises(PermissionError):
        runtime.recover("backend", scope())
    recovered = runtime.recover("backend", scope(), "approval://1")
    assert recovered.status is ServiceStatus.RUNNING
    recovered.status = ServiceStatus.FAILED
    with pytest.raises(RuntimeError, match="Maximum recovery"):
        runtime.recover("backend", scope(), "approval://2")
    recovered.metadata["restriction_active"] = True
    with pytest.raises(RuntimeError, match="restriction or challenge"):
        runtime.recover("backend", scope(), "approval://3")
    assert recovered.health is HealthState.BLOCKED


def test_api_dashboard_telemetry_statistics_and_metrics_contracts() -> None:
    class App:
        def __init__(self) -> None:
            self.routes: dict[str, Any] = {}

        def add_api_route(self, path: str, endpoint: Any, **kwargs: Any) -> None:
            self.routes[path] = endpoint

    runtime = manager()
    runtime.register_service(service("backend"), scope())
    runtime.start(scope())
    app = App()
    register_runtime_manager_routes(app, runtime)
    assert set(ROUTES).issubset(app.routes)
    assert "/tiktok/runtime/dashboard" in app.routes
    assert "/tiktok/runtime/telemetry" in app.routes
    assert runtime.dashboard(scope())["safety"]["challenge_bypass"] is False
    assert runtime.statistics(scope())["availability"] == 1
    metrics = runtime.metrics.render_prometheus()
    assert all(name in metrics for name in METRIC_NAMES)
