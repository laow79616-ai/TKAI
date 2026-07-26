"""Enterprise plugin marketplace orchestration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from threading import RLock
from time import monotonic, time

from tkai.core.exceptions import PluginError

from ..catalog import PluginCatalog
from ..models import InstalledPlugin, PluginDefinition, PluginState
from ..permissions import PermissionPolicy
from ..registry import MarketplaceRegistry


class PluginAuditAction(str, Enum):
    INSTALL = "install"
    UPDATE = "update"
    ENABLE = "enable"
    DISABLE = "disable"
    DELETE = "delete"


@dataclass(frozen=True, slots=True)
class PluginAuditEvent:
    sequence: int
    action: PluginAuditAction
    plugin_id: str
    version: str
    actor: str
    timestamp: float


class PluginMetrics:
    def __init__(self) -> None:
        self._counters = {
            "plugin_install_total": 0,
            "plugin_load_total": 0,
            "plugin_failure_total": 0,
        }
        self._execution_seconds: list[float] = []
        self._lock = RLock()

    def increment(self, name: str) -> None:
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + 1

    def observe_execution(self, seconds: float) -> None:
        with self._lock:
            self._execution_seconds.append(seconds)

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                **self._counters,
                "plugin_execution_seconds": tuple(self._execution_seconds),
            }

    def render_prometheus(self) -> str:
        snapshot = self.snapshot()
        lines = [
            f"{key} {value}"
            for key, value in snapshot.items()
            if key != "plugin_execution_seconds"
        ]
        observations = snapshot["plugin_execution_seconds"]
        assert isinstance(observations, tuple)
        lines.append(f"plugin_execution_seconds_count {len(observations)}")
        lines.append(f"plugin_execution_seconds_sum {sum(observations)}")
        return "\n".join(lines) + "\n"


class EnterprisePluginMarketplace:
    """Coordinate catalog, permissions, installed state, metrics, and audit."""

    def __init__(
        self,
        catalog: PluginCatalog | None = None,
        registry: MarketplaceRegistry | None = None,
        permission_policy: PermissionPolicy | None = None,
        clock: Callable[[], float] = time,
    ) -> None:
        self.catalog = catalog or PluginCatalog()
        self.registry = registry or MarketplaceRegistry()
        self.permission_policy = permission_policy or PermissionPolicy()
        self.metrics = PluginMetrics()
        self._clock = clock
        self._audit: list[PluginAuditEvent] = []

    def register(self, definition: PluginDefinition) -> None:
        self.catalog.publish(definition)

    def install(
        self, plugin_id: str, version: str | None = None, actor: str = "system"
    ) -> InstalledPlugin:
        started = monotonic()
        try:
            definition = self.catalog.get(plugin_id, version)
            self.permission_policy.validate(definition.permissions)
            installed = {
                item.definition.plugin_id: item.definition.version
                for item in self.registry.list()
            }
            missing = [
                dependency.plugin_id
                for dependency in definition.dependencies
                if installed.get(dependency.plugin_id) != dependency.version
            ]
            if missing:
                raise PluginError(f"Unsatisfied plugin dependencies: {sorted(missing)}")
            record = self.registry.install(definition, self._clock())
            self.metrics.increment("plugin_install_total")
            self._record(PluginAuditAction.INSTALL, record, actor)
            return record
        except Exception:
            self.metrics.increment("plugin_failure_total")
            raise
        finally:
            self.metrics.observe_execution(monotonic() - started)

    def uninstall(self, plugin_id: str, actor: str = "system") -> InstalledPlugin:
        record = self.registry.uninstall(plugin_id)
        self._record(PluginAuditAction.DELETE, record, actor)
        return record

    def enable(self, plugin_id: str, actor: str = "system") -> InstalledPlugin:
        record = self.registry.set_state(plugin_id, PluginState.ENABLED)
        self.metrics.increment("plugin_load_total")
        self._record(PluginAuditAction.ENABLE, record, actor)
        return record

    def disable(self, plugin_id: str, actor: str = "system") -> InstalledPlugin:
        record = self.registry.set_state(plugin_id, PluginState.DISABLED)
        self._record(PluginAuditAction.DISABLE, record, actor)
        return record

    def upgrade(
        self, plugin_id: str, version: str | None = None, actor: str = "system"
    ) -> InstalledPlugin:
        definition = self.catalog.get(plugin_id, version)
        self.permission_policy.validate(definition.permissions)
        record = self.registry.upgrade(plugin_id, definition, self._clock())
        self._record(PluginAuditAction.UPDATE, record, actor)
        return record

    def rollback(self, plugin_id: str, actor: str = "system") -> InstalledPlugin:
        record = self.registry.rollback(plugin_id, self._clock())
        self._record(PluginAuditAction.UPDATE, record, actor)
        return record

    def updates(self) -> tuple[PluginDefinition, ...]:
        updates = []
        for item in self.registry.list():
            latest = self.catalog.get(item.definition.plugin_id)
            if latest.version != item.definition.version:
                updates.append(latest)
        return tuple(updates)

    def audit(self) -> tuple[PluginAuditEvent, ...]:
        return tuple(self._audit)

    def _record(
        self, action: PluginAuditAction, record: InstalledPlugin, actor: str
    ) -> None:
        self._audit.append(
            PluginAuditEvent(
                len(self._audit) + 1,
                action,
                record.definition.plugin_id,
                record.definition.version,
                actor,
                self._clock(),
            )
        )


__all__ = (
    "EnterprisePluginMarketplace",
    "PluginAuditAction",
    "PluginAuditEvent",
    "PluginMetrics",
)
