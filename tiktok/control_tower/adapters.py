"""Read-only ports over existing TikTok subsystem snapshots."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
from typing import Any, Protocol

from .models import CONTROL_TOWER_MODULES, ControlTowerScope


class ControlTowerProvider(Protocol):
    def snapshot(self, module: str, scope: ControlTowerScope) -> dict[str, Any]: ...


class ReferenceVault(Protocol):
    def protect(self, value: str, scope: ControlTowerScope) -> str: ...


class LocalReferenceVault:
    """Create opaque scoped references without retaining or logging source values."""

    def __init__(self, key: bytes = b"tkai-control-tower-reference-v1") -> None:
        self._key = key

    def protect(self, value: str, scope: ControlTowerScope) -> str:
        digest = sha256(
            self._key
            + scope.tenant.encode()
            + scope.workspace.encode()
            + value.encode()
        ).hexdigest()
        return f"sealed-ref://{digest}"


class ExistingModuleProvider:
    """Calls injected read-only dashboard adapters; it owns no infrastructure."""

    def __init__(
        self,
        readers: dict[str, Callable[[ControlTowerScope], dict[str, Any]]] | None = None,
    ) -> None:
        self.readers = readers or {}

    def snapshot(self, module: str, scope: ControlTowerScope) -> dict[str, Any]:
        if module not in CONTROL_TOWER_MODULES:
            raise ValueError(f"Unknown TikTok subsystem: {module}")
        reader = self.readers.get(module)
        if reader is None:
            return {
                "health": "unavailable",
                "status": "not_connected",
                "summary": {"source": f"existing:{module}"},
            }
        return reader(scope)


class ExistingServiceRegistryProvider(ExistingModuleProvider):
    """Summarize live in-process services without calling mutating operations."""

    def __init__(self, services: dict[str, object]) -> None:
        super().__init__()
        self.services = dict(services)

    def snapshot(self, module: str, scope: ControlTowerScope) -> dict[str, Any]:
        if module not in CONTROL_TOWER_MODULES:
            return super().snapshot(module, scope)
        service = self.services.get(module)
        if service is None:
            return super().snapshot(module, scope)
        collections = (
            "accounts",
            "alerts",
            "allocations",
            "automations",
            "browsers",
            "devices",
            "executions",
            "plans",
            "processes",
            "proxies",
            "resources",
            "workflows",
        )
        counts = {
            name: len(value)
            for name in collections
            if hasattr(service, name)
            and hasattr((value := getattr(service, name)), "__len__")
        }
        return {
            "health": "healthy",
            "status": "connected",
            "summary": {
                "source": f"existing:{module}",
                "active": float(sum(counts.values())),
                "capacity_percent": 0,
                "records": counts,
            },
        }


class MockControlTowerProvider(ExistingModuleProvider):
    """Deterministic offline provider for local development and tests."""

    def snapshot(self, module: str, scope: ControlTowerScope) -> dict[str, Any]:
        if module not in CONTROL_TOWER_MODULES:
            return super().snapshot(module, scope)
        return {
            "health": "healthy",
            "status": "operational",
            "summary": {
                "source": f"mock-existing:{module}",
                "active": 1,
                "capacity_percent": 25,
            },
        }
