"""Deterministic lifecycle, supervision, recovery, and observability control plane."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from datetime import datetime
from time import perf_counter
from typing import Any

from .adapters import DeterministicLocalPort, RuntimeServicePort
from .metrics import RuntimeMetrics
from .models import (
    HealthState,
    ManagedService,
    RestartMode,
    RuntimeEvent,
    RuntimeInstance,
    RuntimeLimits,
    RuntimeProcess,
    RuntimeScope,
    RuntimeStatus,
    RuntimeWorker,
    ServiceStatus,
    utcnow,
)

TRANSITIONS: dict[RuntimeStatus, frozenset[RuntimeStatus]] = {
    RuntimeStatus.INITIALIZING: frozenset(
        {RuntimeStatus.STARTING, RuntimeStatus.STOPPED}
    ),
    RuntimeStatus.STARTING: frozenset(
        {RuntimeStatus.READY, RuntimeStatus.RECOVERING, RuntimeStatus.STOPPING}
    ),
    RuntimeStatus.READY: frozenset({RuntimeStatus.RUNNING, RuntimeStatus.STOPPING}),
    RuntimeStatus.RUNNING: frozenset(
        {RuntimeStatus.PAUSED, RuntimeStatus.RECOVERING, RuntimeStatus.STOPPING}
    ),
    RuntimeStatus.PAUSED: frozenset(
        {RuntimeStatus.RUNNING, RuntimeStatus.RECOVERING, RuntimeStatus.STOPPING}
    ),
    RuntimeStatus.RECOVERING: frozenset(
        {RuntimeStatus.RUNNING, RuntimeStatus.PAUSED, RuntimeStatus.STOPPING}
    ),
    RuntimeStatus.STOPPING: frozenset({RuntimeStatus.STOPPED}),
    RuntimeStatus.STOPPED: frozenset({RuntimeStatus.STARTING, RuntimeStatus.ARCHIVED}),
    RuntimeStatus.ARCHIVED: frozenset({RuntimeStatus.DELETED}),
    RuntimeStatus.DELETED: frozenset(),
}


class TikTokRuntimeManager:
    """Single-user local runtime manager with isolated, bounded operations."""

    def __init__(
        self,
        runtime: RuntimeInstance,
        ports: dict[str, RuntimeServicePort] | None = None,
        limits: RuntimeLimits | None = None,
    ) -> None:
        runtime.validate()
        self.runtime = runtime
        self.limits = limits or RuntimeLimits()
        self.limits.validate()
        self.ports = ports or {}
        self.fallback_port = DeterministicLocalPort()
        self.services: dict[str, ManagedService] = {}
        self.processes: dict[str, RuntimeProcess] = {}
        self.workers: dict[str, RuntimeWorker] = {}
        self.events: list[RuntimeEvent] = []
        self.recovery_attempts: Counter[str] = Counter()
        self.failure_distribution: Counter[str] = Counter()
        self.startup_duration = 0.0
        self.shutdown_duration = 0.0
        self.started_at: datetime | None = None
        self._locked = False
        self.metrics = RuntimeMetrics()

    @staticmethod
    def _require(scope: RuntimeScope, permission: str) -> None:
        required = f"tiktok:runtime:{permission}"
        if (
            required not in scope.permissions
            and "tiktok:runtime:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {required}")

    def _scope(self, scope: RuntimeScope) -> None:
        if (
            scope.tenant != self.runtime.tenant
            or scope.workspace != self.runtime.workspace
        ):
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _record(
        self,
        scope: RuntimeScope,
        kind: str,
        service_id: str = "",
        detail: str = "",
    ) -> None:
        lowered = detail.casefold()
        if any(
            marker in lowered
            for marker in ("password=", "token=", "cookie=", "secret=")
        ):
            raise ValueError("Secrets are forbidden in runtime audit events.")
        self.events.append(
            RuntimeEvent(
                kind,
                self.runtime.id,
                service_id,
                scope.tenant,
                scope.workspace,
                scope.actor,
                detail,
            )
        )

    def _transition(self, status: RuntimeStatus, scope: RuntimeScope) -> None:
        if status not in TRANSITIONS[self.runtime.status]:
            source = self.runtime.status.value
            raise ValueError(
                f"Invalid runtime transition: {source} -> {status.value}"
            )
        self.runtime.status = status
        self.runtime.updated_at = utcnow()
        self._record(scope, "lifecycle", detail=status.value)

    def register_service(
        self, service: ManagedService, scope: RuntimeScope
    ) -> ManagedService:
        self._require(scope, "manage")
        self._scope(scope)
        if service.tenant != scope.tenant or service.workspace != scope.workspace:
            raise PermissionError("Service scope does not match runtime scope.")
        service.validate(self.limits.maximum_restart_attempts)
        if service.id in self.services:
            raise ValueError("Service ID must be unique.")
        if len(self.services) >= self.limits.maximum_services:
            raise OverflowError("Runtime service limit reached.")
        self.services[service.id] = service
        self.metrics.set("tiktok_runtime_services_total", len(self.services))
        self._record(scope, "registration", service.id)
        self._validate_graph()
        return service

    def _validate_graph(self) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(service_id: str) -> None:
            if service_id in visiting:
                raise ValueError("Service dependency graph contains a cycle.")
            if service_id in visited:
                return
            visiting.add(service_id)
            for dependency in self.services[service_id].dependencies:
                if dependency not in self.services:
                    raise ValueError(f"Unknown service dependency: {dependency}")
                visit(dependency)
            visiting.remove(service_id)
            visited.add(service_id)

        for service_id in self.services:
            visit(service_id)

    def startup_order(self) -> list[str]:
        self._validate_graph()
        ordered: list[str] = []
        seen: set[str] = set()

        def add(service_id: str) -> None:
            if service_id in seen:
                return
            for dependency in sorted(self.services[service_id].dependencies):
                add(dependency)
            seen.add(service_id)
            ordered.append(service_id)

        for service_id in sorted(self.services):
            add(service_id)
        return ordered

    def start(self, scope: RuntimeScope) -> None:
        self._require(scope, "operate")
        self._scope(scope)
        if self._locked:
            raise RuntimeError("A bounded runtime operation is already active.")
        self._locked = True
        started = perf_counter()
        started_services: list[ManagedService] = []
        try:
            self._transition(RuntimeStatus.STARTING, scope)
            for service_id in self.startup_order():
                service = self.services[service_id]
                port = self.ports.get(service_id, self.fallback_port)
                port.validate(service, scope)
                service.status = ServiceStatus.STARTING
                port.start(service, scope)
                if not port.health(service, scope):
                    raise RuntimeError(
                        f"Startup health validation failed: {service.id}"
                    )
                service.status = ServiceStatus.RUNNING
                service.health = HealthState.HEALTHY
                service.heartbeat_at = utcnow()
                started_services.append(service)
                self._record(scope, "startup", service.id)
            self._transition(RuntimeStatus.READY, scope)
            self._transition(RuntimeStatus.RUNNING, scope)
            self.started_at = utcnow()
        except Exception:
            for service in reversed(started_services):
                port = self.ports.get(service.id, self.fallback_port)
                port.stop(service, scope)
                port.cleanup(service, scope)
                service.status = ServiceStatus.STOPPED
            self.failure_distribution["startup"] += 1
            self._record(scope, "failure", detail="startup rollback completed")
            if self.runtime.status is RuntimeStatus.STARTING:
                self._transition(RuntimeStatus.RECOVERING, scope)
            raise
        finally:
            self.startup_duration = perf_counter() - started
            self.metrics.set("tiktok_runtime_startup_seconds", self.startup_duration)
            self._locked = False
            self._update_metrics()

    def stop(self, scope: RuntimeScope) -> None:
        self._require(scope, "operate")
        self._scope(scope)
        if self._locked:
            raise RuntimeError("A bounded runtime operation is already active.")
        self._locked = True
        started = perf_counter()
        try:
            self._transition(RuntimeStatus.STOPPING, scope)
            for service_id in reversed(self.startup_order()):
                service = self.services[service_id]
                if service.status is ServiceStatus.STOPPED:
                    continue
                port = self.ports.get(service_id, self.fallback_port)
                service.status = ServiceStatus.STOPPING
                port.drain(service, scope)
                port.stop(service, scope)
                port.cleanup(service, scope)
                service.status = ServiceStatus.STOPPED
                service.health = HealthState.UNKNOWN
                self._record(scope, "shutdown", service.id)
            self.workers.clear()
            self.processes.clear()
            self._transition(RuntimeStatus.STOPPED, scope)
        finally:
            self.shutdown_duration = perf_counter() - started
            self.metrics.set("tiktok_runtime_shutdown_seconds", self.shutdown_duration)
            self._locked = False
            self._update_metrics()

    def heartbeat(
        self,
        service_id: str,
        healthy: bool,
        latency_seconds: float,
        scope: RuntimeScope,
    ) -> ManagedService:
        self._require(scope, "operate")
        self._scope(scope)
        service = self.services[service_id]
        service.heartbeat_at = utcnow()
        service.health = HealthState.HEALTHY if healthy else HealthState.UNHEALTHY
        if not healthy:
            service.status = ServiceStatus.FAILED
            self.failure_distribution[service_id] += 1
            self._record(scope, "health_change", service_id, "unhealthy")
        self.metrics.set(
            "tiktok_runtime_heartbeat_latency_seconds", max(0, latency_seconds)
        )
        self._update_metrics()
        return service

    def supervise(self, scope: RuntimeScope, now: datetime | None = None) -> list[str]:
        self._require(scope, "operate")
        self._scope(scope)
        current = now or utcnow()
        failed: list[str] = []
        for service in self.services.values():
            latency = (current - service.heartbeat_at).total_seconds()
            if (
                service.status is ServiceStatus.RUNNING
                and latency > self.limits.heartbeat_timeout_seconds
            ):
                service.status = ServiceStatus.FAILED
                service.health = HealthState.UNHEALTHY
                failed.append(service.id)
                self.failure_distribution["heartbeat_timeout"] += 1
                self._record(scope, "failure", service.id, "heartbeat timeout")
        self._update_metrics()
        return failed

    def recover(
        self, service_id: str, scope: RuntimeScope, approval_reference: str = ""
    ) -> ManagedService:
        self._require(scope, "recover")
        self._scope(scope)
        service = self.services[service_id]
        if service.metadata.get("restriction_active") or service.metadata.get(
            "challenge_active"
        ):
            service.health = HealthState.BLOCKED
            self._record(
                scope, "recovery_blocked", service_id, "restriction unresolved"
            )
            raise RuntimeError(
                "Recovery stopped because a TikTok restriction or challenge "
                "is unresolved."
            )
        policy = service.restart_policy
        if policy.mode is RestartMode.NEVER:
            raise RuntimeError("Restart policy forbids recovery.")
        if (
            policy.approval_required or policy.mode is RestartMode.MANUAL_APPROVAL
        ) and not approval_reference:
            raise PermissionError("Manual approval reference is required.")
        attempts = self.recovery_attempts[service_id]
        maximum = min(policy.maximum_attempts, self.limits.maximum_recovery_attempts)
        if attempts >= maximum:
            raise RuntimeError("Maximum recovery attempts reached.")
        self.recovery_attempts[service_id] += 1
        service.status = ServiceStatus.RECOVERING
        port = self.ports.get(service_id, self.fallback_port)
        port.stop(service, scope)
        port.cleanup(service, scope)
        port.validate(service, scope)
        port.start(service, scope)
        if not port.health(service, scope):
            service.status = ServiceStatus.FAILED
            service.health = HealthState.UNHEALTHY
            raise RuntimeError("Service recovery health validation failed.")
        service.status = ServiceStatus.RUNNING
        service.health = HealthState.HEALTHY
        service.restart_count += 1
        service.recovery_count += 1
        service.heartbeat_at = utcnow()
        self.metrics.increment("tiktok_runtime_restart_total")
        self.metrics.increment("tiktok_runtime_recovery_total")
        self._record(scope, "recovery", service_id, approval_reference)
        self._update_metrics()
        return service

    def register_process(
        self, process: RuntimeProcess, scope: RuntimeScope
    ) -> RuntimeProcess:
        self._require(scope, "manage")
        self._scope(scope)
        if process.service_id not in self.services:
            raise ValueError("Process service must be registered.")
        if len(self.processes) >= self.limits.maximum_processes:
            raise OverflowError("Runtime process limit reached.")
        if process.tenant != scope.tenant or process.workspace != scope.workspace:
            raise PermissionError("Process scope does not match runtime scope.")
        self.processes[process.id] = process
        return process

    def register_worker(
        self, worker: RuntimeWorker, scope: RuntimeScope
    ) -> RuntimeWorker:
        self._require(scope, "manage")
        self._scope(scope)
        if worker.service_id not in self.services:
            raise ValueError("Worker service must be registered.")
        if len(self.workers) >= self.limits.maximum_workers:
            raise OverflowError("Runtime worker limit reached.")
        if worker.tenant != scope.tenant or worker.workspace != scope.workspace:
            raise PermissionError("Worker scope does not match runtime scope.")
        self.workers[worker.id] = worker
        return worker

    def health(self, scope: RuntimeScope) -> dict[str, Any]:
        self._require(scope, "read")
        self._scope(scope)
        total = len(self.services)
        healthy = sum(
            item.health is HealthState.HEALTHY for item in self.services.values()
        )
        score = healthy / total if total else 1.0
        return {
            "runtime": self.runtime.status.value,
            "services": {
                key: value.health.value for key, value in self.services.items()
            },
            "registry": "healthy",
            "startup": "healthy"
            if self.runtime.status is not RuntimeStatus.RECOVERING
            else "degraded",
            "shutdown": "healthy"
            if self.runtime.status is RuntimeStatus.STOPPED
            else "not_started",
            "composite": HealthState.HEALTHY.value
            if score == 1
            else HealthState.DEGRADED.value,
            "score": score,
        }

    def _update_metrics(self) -> None:
        running = sum(
            item.status is ServiceStatus.RUNNING for item in self.services.values()
        )
        self.metrics.set("tiktok_runtime_services_total", len(self.services))
        self.metrics.set("tiktok_runtime_running_total", running)
        total = len(self.services)
        healthy = sum(
            item.health is HealthState.HEALTHY for item in self.services.values()
        )
        self.metrics.set("tiktok_runtime_health_score", healthy / total if total else 1)

    def telemetry(self, scope: RuntimeScope) -> dict[str, Any]:
        health = self.health(scope)
        duration = (
            (utcnow() - self.started_at).total_seconds() if self.started_at else 0.0
        )
        return {
            "service_count": len(self.services),
            "running_services": self.metrics.values["tiktok_runtime_running_total"],
            "restart_count": self.metrics.values["tiktok_runtime_restart_total"],
            "recovery_count": self.metrics.values["tiktok_runtime_recovery_total"],
            "heartbeat_latency": self.metrics.values[
                "tiktok_runtime_heartbeat_latency_seconds"
            ],
            "cpu": None,
            "memory": None,
            "runtime_duration": max(0.0, duration),
            "health_score": health["score"],
        }

    def statistics(self, scope: RuntimeScope) -> dict[str, Any]:
        telemetry = self.telemetry(scope)
        count = max(1, len(self.services))
        return {
            "availability": telemetry["health_score"],
            "restart_rate": telemetry["restart_count"] / count,
            "recovery_success": sum(
                item.recovery_count for item in self.services.values()
            ),
            "startup_time": self.startup_duration,
            "shutdown_time": self.shutdown_duration,
            "failure_distribution": dict(self.failure_distribution),
            "service_utilization": telemetry["running_services"] / count,
        }

    def dashboard(self, scope: RuntimeScope) -> dict[str, Any]:
        return {
            "title": "TikTok Runtime Manager",
            "sections": [
                "Runtime Overview",
                "Services",
                "Registry",
                "Processes",
                "Workers",
                "Health",
                "Recovery",
                "Telemetry",
                "Statistics",
            ],
            "runtime": asdict(self.runtime),
            "health": self.health(scope),
            "telemetry": self.telemetry(scope),
            "statistics": self.statistics(scope),
            "safety": {
                "restriction_circumvention": False,
                "challenge_bypass": False,
                "bounded_runtime_operations": True,
            },
        }
