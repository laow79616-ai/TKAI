"""In-process registration, discovery, routing, health, and lifecycle framework."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from dataclasses import replace
from datetime import datetime, timezone
from threading import RLock
from time import monotonic

from tkai.v7.security import (
    AccessController,
    IsolationPolicy,
    Principal,
    filter_secrets,
)
from tkai.v7.service_mesh.contracts import (
    HealthStatus,
    ServiceHealth,
    ServiceMetrics,
    ServiceModel,
    ServiceProvider,
    ServiceStatus,
)


class ServiceMeshError(RuntimeError):
    """Base service mesh error."""


class ServiceNotFoundError(ServiceMeshError, LookupError):
    pass


class ServiceValidationError(ServiceMeshError):
    def __init__(self, errors: Iterable[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("; ".join(self.errors))


class DependencyCycleError(ServiceValidationError):
    pass


class LifecycleTransitionError(ServiceMeshError):
    pass


class RouteNotFoundError(ServiceMeshError, LookupError):
    pass


class AuditLog:
    """Append-only, secret-filtered audit events."""

    def __init__(self) -> None:
        self._records: list[dict[str, object]] = []

    def record(
        self,
        action: str,
        service_id: str,
        actor: str = "system",
        details: Mapping[str, object] | None = None,
    ) -> None:
        self._records.append(
            {
                "timestamp": _now(),
                "action": action,
                "service_id": service_id,
                "actor": actor,
                "details": filter_secrets(details or {}),
            }
        )

    def list(self, service_id: str | None = None) -> tuple[dict[str, object], ...]:
        return tuple(
            dict(record)
            for record in self._records
            if service_id is None or record["service_id"] == service_id
        )


class ServiceMetricsStore:
    def __init__(self) -> None:
        self._values: dict[str, ServiceMetrics] = {}

    def get(self, service_id: str) -> ServiceMetrics:
        return self._values.get(service_id, ServiceMetrics())

    def route(self, service_id: str, latency_ms: float, success: bool) -> None:
        current = self.get(service_id)
        requests = current.requests + 1
        self._values[service_id] = replace(
            current,
            requests=requests,
            successes=current.successes + int(success),
            failures=current.failures + int(not success),
            latency_ms=((current.latency_ms * current.requests) + latency_ms)
            / requests,
            route_count=current.route_count + 1,
        )

    def availability(self, service_id: str, value: float) -> None:
        self._values[service_id] = replace(
            self.get(service_id), availability=max(0.0, min(1.0, value))
        )


class HealthMonitor:
    def __init__(self) -> None:
        self._checks: dict[str, Callable[[], Mapping[str, object] | bool]] = {}
        self._health: dict[str, ServiceHealth] = {}

    def register(
        self,
        service_id: str,
        check: Callable[[], Mapping[str, object] | bool],
    ) -> None:
        self._checks[service_id] = check

    def heartbeat(
        self,
        service_id: str,
        *,
        live: bool = True,
        ready: bool = True,
        diagnostics: Mapping[str, object] | None = None,
    ) -> ServiceHealth:
        available = live and ready
        health = ServiceHealth(
            status=HealthStatus.HEALTHY if available else HealthStatus.DEGRADED,
            live=live,
            ready=ready,
            available=available,
            diagnostics=filter_secrets(diagnostics or {}),
            last_heartbeat=_now(),
        )
        self._health[service_id] = health
        return health

    def check(self, service_id: str) -> ServiceHealth:
        callback = self._checks.get(service_id)
        if callback is None:
            return self._health.get(service_id, ServiceHealth())
        try:
            result = callback()
            if isinstance(result, Mapping):
                return self.heartbeat(
                    service_id,
                    live=bool(result.get("live", True)),
                    ready=bool(result.get("ready", True)),
                    diagnostics=result,
                )
            return self.heartbeat(service_id, live=bool(result), ready=bool(result))
        except Exception as error:  # noqa: BLE001 - providers are isolated here
            health = ServiceHealth(
                status=HealthStatus.UNHEALTHY,
                diagnostics={"error": type(error).__name__},
                last_heartbeat=_now(),
            )
            self._health[service_id] = health
            return health


class DependencyGraph:
    def __init__(self, services: Mapping[str, ServiceModel]) -> None:
        self._services = dict(services)

    def dependencies(self, service_id: str) -> tuple[str, ...]:
        try:
            service = self._services[service_id]
        except KeyError as error:
            raise ServiceNotFoundError(service_id) from error
        return tuple(
            dependency.service_id
            for dependency in service.dependencies
            if dependency.service_id in self._services
        )

    def dependents(self, service_id: str) -> tuple[str, ...]:
        return tuple(
            sorted(
                service.service_id
                for service in self._services.values()
                if service_id in {item.service_id for item in service.dependencies}
            )
        )

    def resolve(self, service_id: str | None = None) -> tuple[str, ...]:
        roots = [service_id] if service_id else sorted(self._services)
        visiting: set[str] = set()
        visited: set[str] = set()
        ordered: list[str] = []

        def visit(current: str) -> None:
            if current in visiting:
                raise DependencyCycleError((f"dependency cycle at {current}",))
            if current in visited:
                return
            if current not in self._services:
                raise ServiceNotFoundError(current)
            visiting.add(current)
            for dependency in self.dependencies(current):
                visit(dependency)
            visiting.remove(current)
            visited.add(current)
            ordered.append(current)

        for root in roots:
            if root is not None:
                visit(root)
        return tuple(ordered)

    def as_dict(self) -> dict[str, tuple[str, ...]]:
        return {
            service_id: self.dependencies(service_id)
            for service_id in sorted(self._services)
        }


class ServiceValidator:
    def validate(
        self,
        service: ServiceModel,
        available: Mapping[str, ServiceModel],
        granted_capabilities: Iterable[str] | None = None,
    ) -> None:
        errors: list[str] = []
        if not service.service_id or any(char.isspace() for char in service.service_id):
            errors.append("service_id must be non-empty and contain no whitespace")
        for field_name in ("name", "description", "owner", "category"):
            if not getattr(service, field_name):
                errors.append(f"{field_name} is required")
        interfaces = {(item.name, item.version) for item in service.interfaces}
        if len(interfaces) != len(service.interfaces):
            errors.append("duplicate interface")
        for dependency in service.dependencies:
            target = available.get(dependency.service_id)
            if target is None:
                if not dependency.optional:
                    errors.append(f"missing dependency: {dependency.service_id}")
                continue
            if not dependency.versions.supports(target.version):
                errors.append(f"incompatible dependency: {dependency.service_id}")
            if dependency.interface and dependency.interface not in {
                item.name for item in target.interfaces
            }:
                errors.append(
                    f"missing interface: {dependency.service_id}:{dependency.interface}"
                )
        if granted_capabilities is not None:
            missing = service.required_capabilities - frozenset(granted_capabilities)
            if missing:
                errors.append(f"capabilities not granted: {', '.join(sorted(missing))}")
        if errors:
            raise ServiceValidationError(errors)


_TRANSITIONS: dict[ServiceStatus, frozenset[ServiceStatus]] = {
    ServiceStatus.REGISTERED: frozenset(
        {ServiceStatus.VALIDATED, ServiceStatus.FAILED}
    ),
    ServiceStatus.VALIDATED: frozenset({ServiceStatus.STARTING, ServiceStatus.FAILED}),
    ServiceStatus.STARTING: frozenset({ServiceStatus.RUNNING, ServiceStatus.FAILED}),
    ServiceStatus.RUNNING: frozenset(
        {
            ServiceStatus.PAUSED,
            ServiceStatus.STOPPING,
            ServiceStatus.FAILED,
            ServiceStatus.DEPRECATED,
        }
    ),
    ServiceStatus.PAUSED: frozenset(
        {ServiceStatus.RUNNING, ServiceStatus.STOPPING, ServiceStatus.FAILED}
    ),
    ServiceStatus.STOPPING: frozenset({ServiceStatus.STOPPED, ServiceStatus.FAILED}),
    ServiceStatus.STOPPED: frozenset({ServiceStatus.STARTING, ServiceStatus.RETIRED}),
    ServiceStatus.FAILED: frozenset(
        {ServiceStatus.STARTING, ServiceStatus.STOPPING, ServiceStatus.RETIRED}
    ),
    ServiceStatus.DEPRECATED: frozenset(
        {ServiceStatus.RUNNING, ServiceStatus.STOPPING, ServiceStatus.RETIRED}
    ),
    ServiceStatus.RETIRED: frozenset(),
}


class ServiceRegistry:
    """Thread-safe internal registry and metadata index."""

    def __init__(self) -> None:
        self._services: dict[str, ServiceModel] = {}
        self._providers: dict[str, ServiceProvider] = {}
        self._indexes: dict[str, dict[str, set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        self._lock = RLock()
        self.validator = ServiceValidator()
        self.health = HealthMonitor()
        self.metrics = ServiceMetricsStore()
        self.audit = AuditLog()

    def register(
        self,
        service: ServiceModel,
        provider: ServiceProvider | None = None,
        *,
        actor: str = "system",
    ) -> ServiceModel:
        with self._lock:
            if service.service_id in self._services:
                raise ValueError(f"service already registered: {service.service_id}")
            registered = replace(
                service,
                status=ServiceStatus.REGISTERED,
                lifecycle=(ServiceStatus.REGISTERED,),
                metadata=filter_secrets(service.metadata),
            )
            self._services[registered.service_id] = registered
            if provider is not None:
                self._providers[registered.service_id] = provider
            self._reindex()
            self.audit.record("registered", registered.service_id, actor)
            return registered

    def get(self, service_id: str) -> ServiceModel:
        try:
            return self._services[service_id]
        except KeyError as error:
            raise ServiceNotFoundError(service_id) from error

    def list(self) -> tuple[ServiceModel, ...]:
        return tuple(self._services[key] for key in sorted(self._services))

    def discover(
        self,
        *,
        category: str | None = None,
        owner: str | None = None,
        status: ServiceStatus | None = None,
        interface: str | None = None,
    ) -> tuple[ServiceModel, ...]:
        return tuple(
            service
            for service in self.list()
            if (category is None or service.category == category)
            and (owner is None or service.owner == owner)
            and (status is None or service.status is status)
            and (
                interface is None
                or interface in {item.name for item in service.interfaces}
            )
        )

    def index(self, field: str, value: str) -> tuple[ServiceModel, ...]:
        return tuple(
            self._services[item]
            for item in sorted(self._indexes.get(field, {}).get(value, set()))
        )

    def graph(self) -> DependencyGraph:
        return DependencyGraph(self._services)

    def validate(
        self,
        service_id: str,
        *,
        granted_capabilities: Iterable[str] | None = None,
        actor: str = "system",
    ) -> ServiceModel:
        service = self.get(service_id)
        self.validator.validate(service, self._services, granted_capabilities)
        self.graph().resolve(service_id)
        return self.transition(service_id, ServiceStatus.VALIDATED, actor=actor)

    def transition(
        self,
        service_id: str,
        target: ServiceStatus,
        *,
        actor: str = "system",
    ) -> ServiceModel:
        with self._lock:
            current = self.get(service_id)
            if target not in _TRANSITIONS[current.status]:
                raise LifecycleTransitionError(
                    f"invalid transition: {current.status.value} -> {target.value}"
                )
            updated = replace(
                current, status=target, lifecycle=(*current.lifecycle, target)
            )
            self._services[service_id] = updated
            self._reindex()
            self.audit.record(target.value, service_id, actor)
            return updated

    def provider(self, service_id: str) -> ServiceProvider:
        try:
            return self._providers[service_id]
        except KeyError as error:
            raise ServiceNotFoundError(f"provider for {service_id}") from error

    def snapshot(self) -> tuple[ServiceModel, ...]:
        return tuple(
            replace(
                service,
                health=self.health.check(service.service_id),
                metrics=self.metrics.get(service.service_id),
                audit=self.audit.list(service.service_id),
            )
            for service in self.list()
        )

    def _reindex(self) -> None:
        self._indexes.clear()
        for service in self._services.values():
            self._indexes["category"][service.category].add(service.service_id)
            self._indexes["owner"][service.owner].add(service.service_id)
            self._indexes["status"][service.status.value].add(service.service_id)
            for interface in service.interfaces:
                self._indexes["interface"][interface.name].add(service.service_id)


class ServiceRouter:
    """Deterministic, reference-only, priority and health-aware routing."""

    def __init__(self, registry: ServiceRegistry) -> None:
        self.registry = registry

    def candidates(
        self,
        interface: str,
        *,
        include_unhealthy: bool = False,
    ) -> tuple[tuple[ServiceModel, str, int], ...]:
        candidates: list[tuple[ServiceModel, str, int]] = []
        for service in self.registry.discover(interface=interface):
            if service.status is not ServiceStatus.RUNNING:
                continue
            health = self.registry.health.check(service.service_id)
            if not include_unhealthy and not health.available:
                continue
            for endpoint in service.endpoints:
                if endpoint.name == interface:
                    candidates.append((service, endpoint.reference, endpoint.priority))
        return tuple(
            sorted(candidates, key=lambda item: (item[2], item[0].service_id, item[1]))
        )

    def route(
        self,
        interface: str,
        *,
        fallback: Iterable[str] = (),
    ) -> str:
        started = monotonic()
        for requested in (interface, *fallback):
            candidates = self.candidates(requested)
            if candidates:
                service, reference, _ = candidates[0]
                self.registry.metrics.route(
                    service.service_id, (monotonic() - started) * 1000, True
                )
                self.registry.audit.record(
                    "routed", service.service_id, details={"interface": requested}
                )
                return reference
        raise RouteNotFoundError(interface)

    def table(self) -> dict[str, tuple[dict[str, object], ...]]:
        interfaces = sorted(
            {
                item.name
                for service in self.registry.list()
                for item in service.interfaces
            }
        )
        return {
            interface: tuple(
                {
                    "service_id": service.service_id,
                    "reference": reference,
                    "priority": priority,
                }
                for service, reference, priority in self.candidates(interface)
            )
            for interface in interfaces
        }


class ServiceLifecycle:
    def __init__(self, registry: ServiceRegistry) -> None:
        self.registry = registry

    def start(
        self,
        service_id: str,
        *,
        granted_capabilities: Iterable[str] | None = None,
        actor: str = "system",
    ) -> ServiceModel:
        for current_id in self.registry.graph().resolve(service_id):
            current = self.registry.get(current_id)
            if current.status is ServiceStatus.REGISTERED:
                current = self.registry.validate(
                    current_id,
                    granted_capabilities=granted_capabilities,
                    actor=actor,
                )
            if current.status is ServiceStatus.RUNNING:
                continue
            if current.status not in {
                ServiceStatus.VALIDATED,
                ServiceStatus.STOPPED,
                ServiceStatus.FAILED,
            }:
                raise LifecycleTransitionError(
                    f"{current_id} cannot start from {current.status.value}"
                )
            self.registry.transition(current_id, ServiceStatus.STARTING, actor=actor)
            try:
                self.registry.provider(current_id).start()
            except Exception:
                self.registry.transition(current_id, ServiceStatus.FAILED, actor=actor)
                raise
            self.registry.transition(current_id, ServiceStatus.RUNNING, actor=actor)
        return self.registry.get(service_id)

    def pause(self, service_id: str, *, actor: str = "system") -> ServiceModel:
        self.registry.provider(service_id).pause()
        return self.registry.transition(service_id, ServiceStatus.PAUSED, actor=actor)

    def resume(self, service_id: str, *, actor: str = "system") -> ServiceModel:
        return self.registry.transition(service_id, ServiceStatus.RUNNING, actor=actor)

    def stop(self, service_id: str, *, actor: str = "system") -> ServiceModel:
        self.registry.transition(service_id, ServiceStatus.STOPPING, actor=actor)
        try:
            self.registry.provider(service_id).stop()
        except Exception:
            self.registry.transition(service_id, ServiceStatus.FAILED, actor=actor)
            raise
        return self.registry.transition(service_id, ServiceStatus.STOPPED, actor=actor)

    def deprecate(self, service_id: str, *, actor: str = "system") -> ServiceModel:
        return self.registry.transition(
            service_id, ServiceStatus.DEPRECATED, actor=actor
        )

    def retire(self, service_id: str, *, actor: str = "system") -> ServiceModel:
        return self.registry.transition(service_id, ServiceStatus.RETIRED, actor=actor)


class ServiceSecurity:
    """RBAC, capability, and service-isolation compatibility facade."""

    def __init__(
        self,
        access: AccessController | None = None,
        isolation: IsolationPolicy | None = None,
    ) -> None:
        self.access = access or AccessController()
        self.isolation = isolation or IsolationPolicy()
        self._service_grants: dict[str, frozenset[str]] = {}

    def grant_services(self, service_id: str, targets: Iterable[str]) -> None:
        self._service_grants[service_id] = frozenset(targets)

    def require_service(self, service_id: str, target: str) -> None:
        if target not in self._service_grants.get(service_id, frozenset()):
            raise PermissionError(f"service {service_id!r} is isolated from {target!r}")

    def require_access(
        self, principal: Principal, permission: str, service_id: str
    ) -> None:
        self.access.require(principal, permission)
        self.require_service(service_id, service_id)


GLOBAL_REGISTRY = ServiceRegistry()
GLOBAL_ROUTER = ServiceRouter(GLOBAL_REGISTRY)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = (
    "GLOBAL_REGISTRY",
    "GLOBAL_ROUTER",
    "AuditLog",
    "DependencyCycleError",
    "DependencyGraph",
    "HealthMonitor",
    "LifecycleTransitionError",
    "RouteNotFoundError",
    "ServiceLifecycle",
    "ServiceMeshError",
    "ServiceMetricsStore",
    "ServiceNotFoundError",
    "ServiceRegistry",
    "ServiceRouter",
    "ServiceSecurity",
    "ServiceValidationError",
    "ServiceValidator",
)
