"""Unified registry and lifecycle implementation."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from dataclasses import replace
from datetime import datetime, timezone
from threading import RLock
from time import monotonic
from typing import Any

from tkai.v7.capabilities.contracts import (
    CapabilityModel,
    CapabilityProvider,
    CapabilityStatus,
    Health,
    HealthStatus,
    Metrics,
)
from tkai.v7.contracts import Version
from tkai.v7.security import filter_secrets


class CapabilityError(RuntimeError):
    """Base framework error."""


class CapabilityValidationError(CapabilityError):
    def __init__(self, errors: Iterable[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("; ".join(self.errors))


class CapabilityNotFoundError(CapabilityError, LookupError):
    pass


class LifecycleTransitionError(CapabilityError):
    pass


class DependencyCycleError(CapabilityValidationError):
    pass


class CapabilityValidator:
    """Validates descriptors without importing or executing providers."""

    def validate(
        self,
        model: CapabilityModel,
        available: Mapping[str, CapabilityModel],
        granted_permissions: Iterable[str] | None = None,
    ) -> None:
        errors: list[str] = []
        if not model.capability_id or any(
            char.isspace() for char in model.capability_id
        ):
            errors.append("capability_id must be non-empty and contain no whitespace")
        if not model.name:
            errors.append("name is required")
        if not model.description:
            errors.append("description is required")
        if not model.owner:
            errors.append("owner is required")
        if not model.category:
            errors.append("category is required")
        if not isinstance(model.version, Version):
            errors.append("version must be semantic")
        interface_keys: set[tuple[str, Version]] = set()
        for interface in model.interfaces:
            key = (interface.name, interface.version)
            if not interface.name:
                errors.append("interface name is required")
            if key in interface_keys:
                errors.append(f"duplicate interface: {interface.name}")
            interface_keys.add(key)
        for dependency in model.dependencies:
            target = available.get(dependency.capability_id)
            if target is None:
                if not dependency.optional:
                    errors.append(f"missing dependency: {dependency.capability_id}")
            elif not dependency.versions.supports(target.version):
                errors.append(
                    f"incompatible dependency: {dependency.capability_id} "
                    f"{target.version}"
                )
        if granted_permissions is not None:
            missing = model.permissions - frozenset(granted_permissions)
            if missing:
                errors.append(f"permissions not granted: {', '.join(sorted(missing))}")
        if not isinstance(model.configuration, Mapping):
            errors.append("configuration must be a mapping")
        if not isinstance(model.metadata, Mapping):
            errors.append("metadata must be a mapping")
        if errors:
            raise CapabilityValidationError(errors)


class DependencyGraph:
    def __init__(self, models: Mapping[str, CapabilityModel]) -> None:
        self._models = dict(models)

    def dependencies(self, capability_id: str) -> tuple[str, ...]:
        try:
            model = self._models[capability_id]
        except KeyError as error:
            raise CapabilityNotFoundError(capability_id) from error
        return tuple(
            dependency.capability_id
            for dependency in model.dependencies
            if dependency.capability_id in self._models
        )

    def dependents(self, capability_id: str) -> tuple[str, ...]:
        return tuple(
            sorted(
                model.capability_id
                for model in self._models.values()
                if capability_id
                in {dependency.capability_id for dependency in model.dependencies}
            )
        )

    def load_order(self, capability_id: str | None = None) -> tuple[str, ...]:
        roots = [capability_id] if capability_id else sorted(self._models)
        visiting: set[str] = set()
        visited: set[str] = set()
        ordered: list[str] = []

        def visit(node: str) -> None:
            if node in visiting:
                raise DependencyCycleError((f"dependency cycle at {node}",))
            if node in visited:
                return
            if node not in self._models:
                raise CapabilityNotFoundError(node)
            visiting.add(node)
            for dependency in self.dependencies(node):
                visit(dependency)
            visiting.remove(node)
            visited.add(node)
            ordered.append(node)

        for root in roots:
            if root is not None:
                visit(root)
        return tuple(ordered)

    def as_dict(self) -> dict[str, tuple[str, ...]]:
        return {
            capability_id: self.dependencies(capability_id)
            for capability_id in sorted(self._models)
        }


class AuditLog:
    """In-memory append-only audit log with recursive secret filtering."""

    def __init__(self) -> None:
        self._records: list[dict[str, object]] = []

    def record(
        self,
        action: str,
        capability_id: str,
        actor: str,
        details: Mapping[str, object] | None = None,
    ) -> None:
        self._records.append(
            {
                "timestamp": _now(),
                "action": action,
                "capability_id": capability_id,
                "actor": actor,
                "details": filter_secrets(details or {}),
            }
        )

    def list(self, capability_id: str | None = None) -> tuple[dict[str, object], ...]:
        return tuple(
            dict(record)
            for record in self._records
            if capability_id is None or record["capability_id"] == capability_id
        )


class CapabilityMetrics:
    def __init__(self) -> None:
        self._values: dict[str, Metrics] = {}

    def get(self, capability_id: str) -> Metrics:
        return self._values.get(capability_id, Metrics())

    def loaded(self, capability_id: str, latency_ms: float) -> None:
        current = self.get(capability_id)
        self._values[capability_id] = replace(
            current,
            load_count=current.load_count + 1,
            latency_ms=latency_ms,
        )

    def activated(self, capability_id: str) -> None:
        current = self.get(capability_id)
        self._values[capability_id] = replace(
            current,
            activation_count=current.activation_count + 1,
            availability=1.0,
        )

    def error(self, capability_id: str) -> None:
        current = self.get(capability_id)
        self._values[capability_id] = replace(current, errors=current.errors + 1)

    def unavailable(self, capability_id: str) -> None:
        self._values[capability_id] = replace(self.get(capability_id), availability=0.0)


class HealthMonitor:
    def __init__(self) -> None:
        self._checks: dict[str, Callable[[], Mapping[str, object] | bool]] = {}
        self._health: dict[str, Health] = {}

    def register(
        self,
        capability_id: str,
        check: Callable[[], Mapping[str, object] | bool],
    ) -> None:
        self._checks[capability_id] = check

    def heartbeat(
        self,
        capability_id: str,
        *,
        ready: bool = True,
        live: bool = True,
        diagnostics: Mapping[str, object] | None = None,
    ) -> Health:
        status = HealthStatus.HEALTHY if ready and live else HealthStatus.DEGRADED
        health = Health(
            status=status,
            ready=ready,
            live=live,
            diagnostics=filter_secrets(diagnostics or {}),
            last_heartbeat=_now(),
        )
        self._health[capability_id] = health
        return health

    def check(self, capability_id: str) -> Health:
        check = self._checks.get(capability_id)
        if check is None:
            return self._health.get(capability_id, Health())
        try:
            result = check()
            if isinstance(result, Mapping):
                return self.heartbeat(
                    capability_id,
                    ready=bool(result.get("ready", True)),
                    live=bool(result.get("live", True)),
                    diagnostics=result,
                )
            return self.heartbeat(capability_id, ready=bool(result), live=bool(result))
        except Exception as error:  # noqa: BLE001 - health checks are provider code
            health = Health(
                status=HealthStatus.UNHEALTHY,
                ready=False,
                live=False,
                diagnostics={"error": type(error).__name__},
                last_heartbeat=_now(),
            )
            self._health[capability_id] = health
            return health


_TRANSITIONS: dict[CapabilityStatus, frozenset[CapabilityStatus]] = {
    CapabilityStatus.REGISTERED: frozenset(
        {CapabilityStatus.VALIDATED, CapabilityStatus.DISABLED}
    ),
    CapabilityStatus.VALIDATED: frozenset(
        {CapabilityStatus.LOADED, CapabilityStatus.DISABLED}
    ),
    CapabilityStatus.LOADED: frozenset(
        {CapabilityStatus.ACTIVE, CapabilityStatus.DISABLED}
    ),
    CapabilityStatus.ACTIVE: frozenset(
        {
            CapabilityStatus.PAUSED,
            CapabilityStatus.DISABLED,
            CapabilityStatus.DEPRECATED,
        }
    ),
    CapabilityStatus.PAUSED: frozenset(
        {CapabilityStatus.ACTIVE, CapabilityStatus.DISABLED}
    ),
    CapabilityStatus.DISABLED: frozenset(
        {CapabilityStatus.VALIDATED, CapabilityStatus.RETIRED}
    ),
    CapabilityStatus.DEPRECATED: frozenset(
        {
            CapabilityStatus.ACTIVE,
            CapabilityStatus.DISABLED,
            CapabilityStatus.RETIRED,
        }
    ),
    CapabilityStatus.RETIRED: frozenset(),
}


class CapabilityRegistry:
    """Thread-safe global registry, index, and dependency graph."""

    def __init__(self) -> None:
        self._models: dict[str, CapabilityModel] = {}
        self._providers: dict[str, CapabilityProvider] = {}
        self._indexes: dict[str, dict[str, set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        self._lock = RLock()
        self.validator = CapabilityValidator()
        self.health = HealthMonitor()
        self.metrics = CapabilityMetrics()
        self.audit = AuditLog()

    def register(
        self,
        model: CapabilityModel,
        provider: CapabilityProvider | None = None,
        *,
        actor: str = "system",
    ) -> CapabilityModel:
        with self._lock:
            if model.capability_id in self._models:
                raise ValueError(
                    f"capability already registered: {model.capability_id}"
                )
            registered = replace(
                model,
                status=CapabilityStatus.REGISTERED,
                lifecycle=(CapabilityStatus.REGISTERED,),
            )
            self._models[registered.capability_id] = registered
            if provider is not None:
                self._providers[registered.capability_id] = provider
            self._index(registered)
            self.audit.record("registered", registered.capability_id, actor)
            return registered

    def unregister(self, capability_id: str) -> None:
        with self._lock:
            model = self.get(capability_id)
            if model.status is not CapabilityStatus.RETIRED:
                raise LifecycleTransitionError(
                    "only retired capabilities can unregister"
                )
            del self._models[capability_id]
            self._providers.pop(capability_id, None)
            self._reindex()

    def get(self, capability_id: str) -> CapabilityModel:
        try:
            return self._models[capability_id]
        except KeyError as error:
            raise CapabilityNotFoundError(capability_id) from error

    def lookup(
        self, capability_id: str, versions: Any | None = None
    ) -> CapabilityModel:
        model = self.get(capability_id)
        if versions is not None and not versions.supports(model.version):
            raise CapabilityNotFoundError(f"{capability_id}@{versions}")
        return model

    def list(self) -> tuple[CapabilityModel, ...]:
        return tuple(self._models[key] for key in sorted(self._models))

    def discover(
        self,
        *,
        category: str | None = None,
        owner: str | None = None,
        status: CapabilityStatus | None = None,
        tags: Iterable[str] = (),
    ) -> tuple[CapabilityModel, ...]:
        required_tags = frozenset(tags)
        return tuple(
            model
            for model in self.list()
            if (category is None or model.category == category)
            and (owner is None or model.owner == owner)
            and (status is None or model.status is status)
            and required_tags.issubset(model.tags)
        )

    def index(self, field: str, value: str) -> tuple[CapabilityModel, ...]:
        return tuple(
            self._models[item]
            for item in sorted(self._indexes.get(field, {}).get(value, set()))
        )

    def graph(self) -> DependencyGraph:
        return DependencyGraph(self._models)

    def validate(
        self,
        capability_id: str,
        *,
        granted_permissions: Iterable[str] | None = None,
        actor: str = "system",
    ) -> CapabilityModel:
        model = self.get(capability_id)
        self.validator.validate(model, self._models, granted_permissions)
        self.graph().load_order(capability_id)
        return self.transition(capability_id, CapabilityStatus.VALIDATED, actor=actor)

    def transition(
        self,
        capability_id: str,
        target: CapabilityStatus,
        *,
        actor: str = "system",
    ) -> CapabilityModel:
        with self._lock:
            current = self.get(capability_id)
            if target not in _TRANSITIONS[current.status]:
                raise LifecycleTransitionError(
                    f"invalid transition: {current.status.value} -> {target.value}"
                )
            updated = replace(
                current,
                status=target,
                lifecycle=(*current.lifecycle, target),
            )
            self._models[capability_id] = updated
            self._reindex()
            self.audit.record(target.value, capability_id, actor)
            if target in {
                CapabilityStatus.DISABLED,
                CapabilityStatus.RETIRED,
                CapabilityStatus.PAUSED,
            }:
                self.metrics.unavailable(capability_id)
            return updated

    def provider(self, capability_id: str) -> CapabilityProvider:
        try:
            return self._providers[capability_id]
        except KeyError as error:
            raise CapabilityNotFoundError(f"provider for {capability_id}") from error

    def snapshot(self) -> tuple[CapabilityModel, ...]:
        return tuple(
            replace(
                model,
                health=self.health.check(model.capability_id),
                metrics=self.metrics.get(model.capability_id),
                audit=self.audit.list(model.capability_id),
            )
            for model in self.list()
        )

    def _index(self, model: CapabilityModel) -> None:
        self._indexes["category"][model.category].add(model.capability_id)
        self._indexes["owner"][model.owner].add(model.capability_id)
        self._indexes["status"][model.status.value].add(model.capability_id)
        for tag in model.tags:
            self._indexes["tag"][tag].add(model.capability_id)

    def _reindex(self) -> None:
        self._indexes.clear()
        for model in self._models.values():
            self._index(model)


class CapabilityLoader:
    """Loads validated providers in deterministic dependency order."""

    def __init__(self, registry: CapabilityRegistry) -> None:
        self.registry = registry

    def load(
        self,
        capability_id: str,
        *,
        granted_permissions: Iterable[str] | None = None,
        actor: str = "system",
    ) -> CapabilityModel:
        for current_id in self.registry.graph().load_order(capability_id):
            current = self.registry.get(current_id)
            if current.status is CapabilityStatus.REGISTERED:
                current = self.registry.validate(
                    current_id,
                    granted_permissions=granted_permissions,
                    actor=actor,
                )
            if current.status is CapabilityStatus.LOADED:
                continue
            if current.status is not CapabilityStatus.VALIDATED:
                raise LifecycleTransitionError(
                    f"{current_id} is not loadable from {current.status.value}"
                )
            started = monotonic()
            try:
                self.registry.provider(current_id).load()
            except Exception:
                self.registry.metrics.error(current_id)
                self.registry.audit.record("load_failed", current_id, actor)
                raise
            latency = (monotonic() - started) * 1000
            self.registry.metrics.loaded(current_id, latency)
            self.registry.transition(current_id, CapabilityStatus.LOADED, actor=actor)
        return self.registry.get(capability_id)

    def activate(self, capability_id: str, *, actor: str = "system") -> CapabilityModel:
        model = self.registry.get(capability_id)
        if model.status in {
            CapabilityStatus.PAUSED,
            CapabilityStatus.LOADED,
        }:
            provider = self.registry.provider(capability_id)
        else:
            raise LifecycleTransitionError(
                f"{capability_id} is not activatable from {model.status.value}"
            )
        try:
            provider.activate()
        except Exception:
            self.registry.metrics.error(capability_id)
            raise
        self.registry.metrics.activated(capability_id)
        return self.registry.transition(
            capability_id, CapabilityStatus.ACTIVE, actor=actor
        )


class CapabilityLifecycle:
    """Coordinates provider callbacks with guarded state transitions."""

    def __init__(self, registry: CapabilityRegistry) -> None:
        self.registry = registry

    def pause(self, capability_id: str, *, actor: str = "system") -> CapabilityModel:
        model = self.registry.get(capability_id)
        if model.status is not CapabilityStatus.ACTIVE:
            raise LifecycleTransitionError(f"{capability_id} is not active")
        self.registry.provider(capability_id).pause()
        return self.registry.transition(
            capability_id, CapabilityStatus.PAUSED, actor=actor
        )

    def disable(self, capability_id: str, *, actor: str = "system") -> CapabilityModel:
        model = self.registry.get(capability_id)
        if CapabilityStatus.DISABLED not in _TRANSITIONS[model.status]:
            raise LifecycleTransitionError(
                f"{capability_id} cannot be disabled from {model.status.value}"
            )
        provider = self.registry._providers.get(capability_id)
        if provider is not None:
            provider.disable()
        return self.registry.transition(
            capability_id, CapabilityStatus.DISABLED, actor=actor
        )

    def deprecate(
        self, capability_id: str, *, actor: str = "system"
    ) -> CapabilityModel:
        return self.registry.transition(
            capability_id, CapabilityStatus.DEPRECATED, actor=actor
        )

    def retire(self, capability_id: str, *, actor: str = "system") -> CapabilityModel:
        return self.registry.transition(
            capability_id, CapabilityStatus.RETIRED, actor=actor
        )


GLOBAL_REGISTRY = CapabilityRegistry()


def compatible(current: Version, requested: Version) -> bool:
    """Semantic compatibility: same major, current is at least requested."""
    return current.major == requested.major and current >= requested


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = (
    "GLOBAL_REGISTRY",
    "AuditLog",
    "CapabilityError",
    "CapabilityLifecycle",
    "CapabilityLoader",
    "CapabilityMetrics",
    "CapabilityNotFoundError",
    "CapabilityRegistry",
    "CapabilityValidationError",
    "CapabilityValidator",
    "DependencyCycleError",
    "DependencyGraph",
    "HealthMonitor",
    "LifecycleTransitionError",
    "compatible",
)
