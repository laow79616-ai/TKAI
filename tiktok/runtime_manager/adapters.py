"""Ports that reuse existing local runtime and TikTok module infrastructure."""

from __future__ import annotations

from typing import Protocol

from .models import ManagedService, RuntimeScope


class RuntimeServicePort(Protocol):
    def validate(self, service: ManagedService, scope: RuntimeScope) -> None: ...
    def start(self, service: ManagedService, scope: RuntimeScope) -> None: ...
    def health(self, service: ManagedService, scope: RuntimeScope) -> bool: ...
    def drain(self, service: ManagedService, scope: RuntimeScope) -> None: ...
    def stop(self, service: ManagedService, scope: RuntimeScope) -> None: ...
    def cleanup(self, service: ManagedService, scope: RuntimeScope) -> None: ...


class DeterministicLocalPort:
    """Offline default used for tests and explicit local embedding."""

    def validate(self, service: ManagedService, scope: RuntimeScope) -> None:
        return None

    def start(self, service: ManagedService, scope: RuntimeScope) -> None:
        return None

    def health(self, service: ManagedService, scope: RuntimeScope) -> bool:
        return True

    def drain(self, service: ManagedService, scope: RuntimeScope) -> None:
        return None

    def stop(self, service: ManagedService, scope: RuntimeScope) -> None:
        return None

    def cleanup(self, service: ManagedService, scope: RuntimeScope) -> None:
        return None


MANAGED_SERVICE_NAMES = (
    "backend",
    "dashboard",
    "ai_studio",
    "browser_cluster",
    "browser_runtime",
    "device_center",
    "task_scheduler",
    "resource_center",
    "workflow_center",
    "automation_engine",
    "operations_center",
    "risk_control_center",
    "analytics_center",
    "health_service",
)
