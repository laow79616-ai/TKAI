"""Read-only diagnostics for AI provider framework configuration and wiring."""

from __future__ import annotations

import asyncio
import json
import platform
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from tkai.cache import CacheManager
from tkai.circuit_breaker import CircuitBreakerManager, CircuitState
from tkai.configuration import ConfigurationManager
from tkai.credentials import CredentialManager
from tkai.health import HealthManager, HealthStatus
from tkai.load import LoadAwareStrategy, LoadManager, LoadStatus
from tkai.observability import (
    EventBus,
    EventDispatcher,
    LoggerAdapter,
    MetricsAdapter,
    TraceAdapter,
)
from tkai.plugins import PluginManager
from tkai.providers.http import AsyncHTTPTransport
from tkai.rate_limit import RateLimitAwareStrategy, RateLimitManager
from tkai.routing import RoutingManager

from .fallback import FallbackCandidate, FallbackEngine, FallbackPolicy
from .manager import ProviderManager
from .models import ProviderCapabilities, ProviderConfig
from .runtime import ProviderRuntime
from .sync_bridge import SyncBridge
from .transport_adapter import TransportAdapter, resolve_transport


class DoctorStatus(str, Enum):
    """Severity of one read-only framework diagnostic."""

    PASS = "PASS"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class DoctorCheck:
    """One diagnostic result with a safe, optional machine-readable detail map."""

    name: str
    status: DoctorStatus
    message: str
    detail: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation with a string status value."""
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass(frozen=True, slots=True)
class DoctorReport:
    """Complete immutable diagnostic report with JSON and text renderers."""

    checks: tuple[DoctorCheck, ...]

    @property
    def passed(self) -> int:
        """Return the number of passing checks."""
        return sum(check.status is DoctorStatus.PASS for check in self.checks)

    @property
    def warnings(self) -> int:
        """Return the number of warning checks."""
        return sum(check.status is DoctorStatus.WARNING for check in self.checks)

    @property
    def errors(self) -> int:
        """Return the number of error checks."""
        return sum(check.status is DoctorStatus.ERROR for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        """Return a stable JSON-ready report without hidden runtime objects."""
        return {
            "summary": {
                "passed": self.passed,
                "warnings": self.warnings,
                "errors": self.errors,
            },
            "checks": [check.to_dict() for check in self.checks],
        }

    def to_json(self) -> str:
        """Serialize the report in stable, human-safe JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)

    def to_text(self) -> str:
        """Render a concise, deterministic report for terminal or log output."""
        lines = [
            "TKAI AI Doctor",
            f"PASS={self.passed} WARNING={self.warnings} ERROR={self.errors}",
        ]
        for check in self.checks:
            detail = f" ({json.dumps(dict(check.detail), sort_keys=True)})"
            lines.append(
                f"[{check.status.value}] {check.name}: {check.message}{detail}"
            )
        return "\n".join(lines)


class DoctorService:
    """Run deterministic, read-only AI provider diagnostics without network access.

    Supplied objects are inspected only. The service never calls provider
    initialization, health endpoints, request methods, close methods, or any
    operation that changes registry, runtime, transport, or fallback state.
    """

    def __init__(
        self,
        manager: ProviderManager | None = None,
        *,
        transports: Iterable[object] = (),
        runtimes: Iterable[ProviderRuntime] = (),
        adapters: Iterable[object] = (),
        bridges: Iterable[SyncBridge] = (),
        fallback: FallbackEngine | FallbackPolicy | None = None,
        fallback_candidates: Sequence[FallbackCandidate[object]] = (),
        credentials: CredentialManager | None = None,
        persistent_configuration: ConfigurationManager | None = None,
        health: HealthManager | None = None,
        observability_bus: EventBus | None = None,
        observability_dispatcher: EventDispatcher | None = None,
        metrics_adapter: MetricsAdapter | None = None,
        logger_adapter: LoggerAdapter | None = None,
        trace_adapter: TraceAdapter | None = None,
        circuit_breaker: CircuitBreakerManager | None = None,
        routing: RoutingManager | None = None,
        load: LoadManager | None = None,
        rate_limit: RateLimitManager | None = None,
        cache: CacheManager | None = None,
        plugins: PluginManager | None = None,
    ) -> None:
        self.manager = manager
        self._transports = tuple(transports)
        self._runtimes = tuple(runtimes)
        self._adapters = tuple(adapters)
        self._bridges = tuple(bridges)
        self._fallback = fallback
        self._fallback_candidates = tuple(fallback_candidates)
        self._credentials = credentials
        self._persistent_configuration = persistent_configuration
        self._health = health
        self._observability_bus = observability_bus
        self._observability_dispatcher = observability_dispatcher
        self._metrics_adapter = metrics_adapter
        self._logger_adapter = logger_adapter
        self._trace_adapter = trace_adapter
        self._circuit_breaker = circuit_breaker
        self._routing = routing
        self._load = load
        self._rate_limit = rate_limit
        self._cache = cache
        self._plugins = plugins

    def run(self) -> DoctorReport:
        """Run every diagnostic once and return a complete immutable report."""
        checks = [*self._environment_checks(), *self._provider_checks()]
        checks.extend(self._configuration_checks())
        checks.extend(self._capability_checks())
        checks.extend(self._transport_checks())
        checks.extend(self._runtime_checks())
        checks.extend(self._fallback_checks())
        checks.extend(self._credential_checks())
        checks.extend(self._persistent_configuration_checks())
        checks.extend(self._health_checks())
        checks.extend(self._observability_checks())
        checks.extend(self._circuit_breaker_checks())
        checks.extend(self._routing_checks())
        checks.extend(self._load_checks())
        checks.extend(self._rate_limit_checks())
        checks.extend(self._cache_checks())
        checks.extend(self._plugin_checks())
        return DoctorReport(tuple(checks))

    def validate_config(self) -> DoctorReport:
        """Run only provider registry, configuration, and capability diagnostics."""
        checks = [*self._provider_checks(), *self._configuration_checks()]
        checks.extend(self._capability_checks())
        return DoctorReport(tuple(checks))

    @staticmethod
    def _environment_checks() -> tuple[DoctorCheck, ...]:
        """Describe local interpreter, operating system, and loop availability."""
        try:
            asyncio.get_running_loop()
            loop_message = "An event loop is currently running"
        except RuntimeError:
            loop_message = "No event loop is currently running"
        return (
            DoctorCheck(
                "environment.python",
                DoctorStatus.PASS,
                "Python interpreter is available",
                {"version": platform.python_version()},
            ),
            DoctorCheck(
                "environment.os",
                DoctorStatus.PASS,
                "Operating system information is available",
                {"system": platform.system(), "platform": sys.platform},
            ),
            DoctorCheck(
                "environment.event_loop",
                DoctorStatus.PASS,
                loop_message,
                {"running": "running" in loop_message},
            ),
        )

    def _provider_checks(self) -> tuple[DoctorCheck, ...]:
        """Check provider registration, default selection, and aliases safely."""
        if self.manager is None:
            return (
                DoctorCheck(
                    "provider.registry",
                    DoctorStatus.WARNING,
                    "No ProviderManager was supplied",
                ),
            )
        names = self.manager.names()
        aliases = self.manager.aliases()
        issues: list[str] = []
        if len(names) != len(set(names)):
            issues.append("duplicate provider names")
        conflicting_aliases = sorted(set(names).intersection(aliases))
        if conflicting_aliases:
            issues.append(
                "aliases conflict with providers: " f"{', '.join(conflicting_aliases)}"
            )
        unknown_targets = sorted(set(aliases.values()).difference(names))
        if unknown_targets:
            issues.append(
                "aliases target unknown providers: " f"{', '.join(unknown_targets)}"
            )
        if issues:
            return (
                DoctorCheck(
                    "provider.registry",
                    DoctorStatus.ERROR,
                    "; ".join(issues),
                    {"providers": names, "aliases": sorted(aliases)},
                ),
            )
        default = self.manager.default_provider
        if not names:
            return (
                DoctorCheck(
                    "provider.registry",
                    DoctorStatus.WARNING,
                    "No providers are registered",
                ),
            )
        if default not in names:
            return (
                DoctorCheck(
                    "provider.registry",
                    DoctorStatus.ERROR,
                    "Default provider is not registered",
                    {"providers": names, "default_provider": default},
                ),
            )
        return (
            DoctorCheck(
                "provider.registry",
                DoctorStatus.PASS,
                "Provider registry and aliases are consistent",
                {
                    "providers": names,
                    "default_provider": default,
                    "aliases": sorted(aliases),
                },
            ),
        )

    def _configuration_checks(self) -> tuple[DoctorCheck, ...]:
        """Validate exposed provider config metadata without rendering secrets."""
        if self.manager is None:
            return ()
        checks: list[DoctorCheck] = []
        for name in self.manager.names():
            config = getattr(self.manager.get(name), "config", None)
            if not isinstance(config, ProviderConfig):
                checks.append(
                    DoctorCheck(
                        f"configuration.{name}",
                        DoctorStatus.WARNING,
                        "Provider has no ProviderConfig metadata",
                    )
                )
                continue
            detail = {
                "base_url_configured": config.base_url is not None,
                "timeout": config.timeout,
                "model_configured": config.model is not None,
                "api_key_configured": config.api_key is not None,
            }
            try:
                config.validate()
            except ValueError as error:
                checks.append(
                    DoctorCheck(
                        f"configuration.{name}",
                        DoctorStatus.ERROR,
                        f"Provider configuration is invalid: {type(error).__name__}",
                        detail,
                    )
                )
                continue
            status = DoctorStatus.PASS if config.api_key else DoctorStatus.WARNING
            message = (
                "Provider configuration is valid"
                if config.api_key
                else "Provider configuration is valid but no API key is configured"
            )
            checks.append(DoctorCheck(f"configuration.{name}", status, message, detail))
        return tuple(checks)

    def _capability_checks(self) -> tuple[DoctorCheck, ...]:
        """Check provider/model capability declarations and routing references."""
        if self.manager is None or not self.manager.names():
            return (
                DoctorCheck(
                    "capability.routing",
                    DoctorStatus.WARNING,
                    "No registered providers are available for capability routing",
                ),
            )
        checks: list[DoctorCheck] = []
        for name in self.manager.names():
            try:
                capabilities = self.manager.registry.capabilities_for(name)
                overrides = self.manager.model_capabilities(name)
            except Exception as error:
                checks.append(
                    DoctorCheck(
                        f"capability.{name}",
                        DoctorStatus.ERROR,
                        f"Capability metadata is unavailable: {type(error).__name__}",
                    )
                )
                continue
            if not isinstance(capabilities, ProviderCapabilities) or any(
                not isinstance(value, ProviderCapabilities)
                for value in overrides.values()
            ):
                checks.append(
                    DoctorCheck(
                        f"capability.{name}",
                        DoctorStatus.ERROR,
                        "Capability declaration has an invalid type",
                    )
                )
                continue
            checks.append(
                DoctorCheck(
                    f"capability.{name}",
                    DoctorStatus.PASS,
                    "Provider and model capability declarations are valid",
                    {
                        "provider_capabilities": sorted(
                            item.value for item in capabilities.supported()
                        ),
                        "model_overrides": sorted(overrides),
                    },
                )
            )
        return tuple(checks)

    def _transport_checks(self) -> tuple[DoctorCheck, ...]:
        """Inspect transport shape and adaptation without issuing any request."""
        transports = list(self._transports)
        if self.manager is not None:
            for name in self.manager.names():
                runtime = getattr(self.manager.get(name), "_runtime", None)
                if runtime is not None:
                    transports.append(getattr(runtime, "transport", None))
        unique = self._unique_objects(item for item in transports if item is not None)
        if not unique:
            return (
                DoctorCheck(
                    "transport", DoctorStatus.WARNING, "No transport was supplied"
                ),
            )
        checks: list[DoctorCheck] = []
        for index, transport in enumerate(unique):
            name = f"transport.{index}"
            if isinstance(transport, AsyncHTTPTransport):
                checks.append(
                    DoctorCheck(
                        name, DoctorStatus.PASS, "AsyncHTTPTransport is configured"
                    )
                )
            elif isinstance(transport, TransportAdapter):
                checks.append(
                    DoctorCheck(
                        name,
                        DoctorStatus.PASS,
                        "Legacy transport is wrapped by TransportAdapter",
                    )
                )
            elif callable(transport):
                resolved, _ = resolve_transport(transport, timeout=1.0)
                checks.append(
                    DoctorCheck(
                        name,
                        DoctorStatus.PASS,
                        "Legacy transport can be resolved to AsyncTransport",
                        {"resolved_type": type(resolved).__name__},
                    )
                )
            elif all(
                hasattr(transport, method) for method in ("request", "stream", "close")
            ):
                checks.append(
                    DoctorCheck(
                        name, DoctorStatus.PASS, "AsyncTransport protocol is present"
                    )
                )
            else:
                checks.append(
                    DoctorCheck(
                        name,
                        DoctorStatus.ERROR,
                        "Transport does not implement the AsyncTransport protocol",
                        {"type": type(transport).__name__},
                    )
                )
        return tuple(checks)

    def _runtime_checks(self) -> tuple[DoctorCheck, ...]:
        """Inspect runtime, adapter, and bridge wiring without changing lifecycle."""
        runtimes = list(self._runtimes)
        adapters = list(self._adapters)
        bridges = list(self._bridges)
        if self.manager is not None:
            for name in self.manager.names():
                provider = self.manager.get(name)
                runtime = getattr(provider, "_runtime", None)
                adapter = getattr(provider, "_adapter", None)
                bridge = getattr(provider, "_bridge", None)
                if runtime is not None:
                    runtimes.append(runtime)
                if adapter is not None:
                    adapters.append(adapter)
                if bridge is not None:
                    bridges.append(bridge)
        runtime_values = self._unique_objects(runtimes)
        adapter_values = self._unique_objects(adapters)
        bridge_values = self._unique_objects(bridges)
        checks: list[DoctorCheck] = []
        if not runtime_values:
            checks.append(
                DoctorCheck(
                    "runtime", DoctorStatus.WARNING, "No ProviderRuntime was supplied"
                )
            )
        for index, runtime in enumerate(runtime_values):
            if not isinstance(runtime, ProviderRuntime):
                checks.append(
                    DoctorCheck(
                        f"runtime.{index}",
                        DoctorStatus.ERROR,
                        "Runtime is not a ProviderRuntime instance",
                    )
                )
                continue
            checks.append(
                DoctorCheck(
                    f"runtime.{index}",
                    DoctorStatus.PASS,
                    "ProviderRuntime wiring is available",
                    {
                        "state": runtime.state.name.lower(),
                        "ownership": runtime.ownership.name.lower(),
                        "retry_budget": runtime.retry.policy.max_retries,
                    },
                )
            )
        if adapter_values:
            checks.append(
                DoctorCheck(
                    "runtime.adapter",
                    DoctorStatus.PASS,
                    "Runtime adapter wiring is available",
                    {"count": len(adapter_values)},
                )
            )
        else:
            checks.append(
                DoctorCheck(
                    "runtime.adapter",
                    DoctorStatus.WARNING,
                    "No runtime adapter was supplied",
                )
            )
        if bridge_values:
            checks.append(
                DoctorCheck(
                    "runtime.sync_bridge",
                    DoctorStatus.PASS,
                    "SyncBridge wiring is available",
                    {"count": len(bridge_values)},
                )
            )
        else:
            checks.append(
                DoctorCheck(
                    "runtime.sync_bridge",
                    DoctorStatus.WARNING,
                    "No SyncBridge was supplied",
                )
            )
        return tuple(checks)

    def _fallback_checks(self) -> tuple[DoctorCheck, ...]:
        """Inspect fallback policy and candidate ordering without executing either."""
        policy = self._fallback_policy()
        if policy is None:
            return (
                DoctorCheck(
                    "fallback", DoctorStatus.WARNING, "No FallbackPolicy was supplied"
                ),
            )
        names = [candidate.name for candidate in self._fallback_candidates]
        duplicate_names = sorted({name for name in names if names.count(name) > 1})
        if duplicate_names:
            return (
                DoctorCheck(
                    "fallback",
                    DoctorStatus.ERROR,
                    "Fallback candidate names are duplicated",
                    {"duplicates": duplicate_names},
                ),
            )
        blocked = sorted(policy.blocked_providers)
        eligible = [name for name in names if name not in policy.blocked_providers]
        status = DoctorStatus.PASS if not names or eligible else DoctorStatus.WARNING
        message = (
            "Fallback policy and candidate order are valid"
            if status is DoctorStatus.PASS
            else "All supplied fallback candidates are blacklisted"
        )
        return (
            DoctorCheck(
                "fallback",
                status,
                message,
                {
                    "max_attempts": policy.max_attempts,
                    "retry_budget": policy.retry_budget,
                    "blacklist": blocked,
                    "candidates": names,
                },
            ),
        )

    def _fallback_policy(self) -> FallbackPolicy | None:
        """Return an injected policy without creating or changing fallback state."""
        if isinstance(self._fallback, FallbackEngine):
            return self._fallback.policy
        if isinstance(self._fallback, FallbackPolicy):
            return self._fallback
        return None

    def _credential_checks(self) -> tuple[DoctorCheck, ...]:
        """Inspect configured local credentials without rendering key material."""
        if self._credentials is None:
            return (
                DoctorCheck(
                    "credentials",
                    DoctorStatus.WARNING,
                    "No CredentialManager was supplied",
                ),
            )
        checks: list[DoctorCheck] = []
        for provider in self._credentials.resolver.providers():
            sources = self._credentials.resolver.sources_for(provider)
            try:
                credential = self._credentials.get(provider)
            except Exception as error:
                checks.append(
                    DoctorCheck(
                        f"credentials.{provider}",
                        DoctorStatus.ERROR,
                        f"Credential resolution failed: {type(error).__name__}",
                    )
                )
                continue
            status = DoctorStatus.WARNING if len(sources) > 1 else DoctorStatus.PASS
            message = (
                "Duplicate credential sources detected"
                if len(sources) > 1
                else "Credential is configured"
            )
            checks.append(
                DoctorCheck(
                    f"credentials.{provider}",
                    status,
                    message,
                    {
                        "source": credential.source,
                        "configured": True,
                        "masked": credential.masked(),
                        "sources": sources,
                    },
                )
            )
        return tuple(checks) or (
            DoctorCheck(
                "credentials", DoctorStatus.WARNING, "No credentials are configured"
            ),
        )

    def _persistent_configuration_checks(self) -> tuple[DoctorCheck, ...]:
        """Inspect local configuration source metadata without exposing values."""
        if self._persistent_configuration is None:
            return (
                DoctorCheck(
                    "persistent_configuration",
                    DoctorStatus.WARNING,
                    "No persistent configuration is supplied",
                ),
            )
        config = self._persistent_configuration.list()
        if not config.data:
            return (
                DoctorCheck(
                    "persistent_configuration",
                    DoctorStatus.WARNING,
                    "Configuration is empty",
                    {
                        "source": config.source,
                        "override_chain": list(config.overrides),
                        "loaded_files": [],
                    },
                ),
            )
        duplicates = len(config.overrides) != len(set(config.overrides))
        status = DoctorStatus.ERROR if duplicates else DoctorStatus.PASS
        message = (
            "Duplicate configuration sources"
            if duplicates
            else "Configuration is loaded"
        )
        return (
            DoctorCheck(
                "persistent_configuration",
                status,
                message,
                {
                    "source": config.source,
                    "override_chain": list(config.overrides),
                    "loaded_files": [
                        item
                        for item in config.overrides
                        if item in {"workspace", "user"}
                    ],
                },
            ),
        )

    def _health_checks(self) -> tuple[DoctorCheck, ...]:
        """Report passive health snapshots without probing any provider."""
        if self._health is None:
            return (
                DoctorCheck(
                    "health", DoctorStatus.WARNING, "No HealthManager was supplied"
                ),
            )
        checks: list[DoctorCheck] = []
        for snapshot in self._health.registry.list():
            status = (
                DoctorStatus.PASS
                if snapshot.status is HealthStatus.HEALTHY
                else (
                    DoctorStatus.WARNING
                    if snapshot.status in {HealthStatus.UNKNOWN, HealthStatus.DEGRADED}
                    else DoctorStatus.ERROR
                )
            )
            checks.append(
                DoctorCheck(
                    f"health.{snapshot.provider}",
                    status,
                    snapshot.status.value,
                    {
                        "requests": snapshot.statistics.requests,
                        "success": snapshot.statistics.success,
                        "failure": snapshot.statistics.failure,
                        "timeout": snapshot.statistics.timeout,
                        "consecutive_failures": snapshot.consecutive_failures,
                        "recent_events": [
                            event.event
                            for event in self._health.collector.events[-5:]
                            if event.provider == snapshot.provider
                        ],
                    },
                )
            )
        return tuple(checks) or (
            DoctorCheck("health", DoctorStatus.WARNING, "No passive health records"),
        )

    def _observability_checks(self) -> tuple[DoctorCheck, ...]:
        """Inspect observability wiring and retained event summaries read-only."""
        checks: list[DoctorCheck] = []
        bus = self._observability_bus
        dispatcher = self._observability_dispatcher
        if bus is None:
            checks.append(
                DoctorCheck(
                    "observability.event_bus",
                    DoctorStatus.WARNING,
                    "No EventBus was supplied",
                )
            )
        else:
            checks.append(
                DoctorCheck(
                    "observability.event_bus",
                    DoctorStatus.PASS,
                    "EventBus is available",
                    {
                        "event_count": len(bus.events),
                        "recent_events": [event.name for event in bus.events[-5:]],
                    },
                )
            )
        if dispatcher is None:
            checks.extend(
                (
                    DoctorCheck(
                        "observability.dispatcher",
                        DoctorStatus.WARNING,
                        "No EventDispatcher was supplied",
                    ),
                    DoctorCheck(
                        "observability.subscribers",
                        DoctorStatus.WARNING,
                        "No subscribers are registered",
                        {"count": 0},
                    ),
                )
            )
        else:
            count = len(dispatcher.subscribers)
            checks.extend(
                (
                    DoctorCheck(
                        "observability.dispatcher",
                        DoctorStatus.PASS,
                        "EventDispatcher is available",
                        {"subscriber_count": count},
                    ),
                    DoctorCheck(
                        "observability.subscribers",
                        DoctorStatus.PASS if count else DoctorStatus.WARNING,
                        (
                            "Subscribers are registered"
                            if count
                            else "No subscribers are registered"
                        ),
                        {"count": count},
                    ),
                )
            )
        for name, adapter in (
            ("metrics", self._metrics_adapter),
            ("logger", self._logger_adapter),
            ("trace", self._trace_adapter),
        ):
            checks.append(
                DoctorCheck(
                    f"observability.{name}",
                    DoctorStatus.PASS if adapter is not None else DoctorStatus.WARNING,
                    (
                        f"{name.title()} adapter is available"
                        if adapter is not None
                        else f"No {name.title()} adapter was supplied"
                    ),
                )
            )
        return tuple(checks)

    def _circuit_breaker_checks(self) -> tuple[DoctorCheck, ...]:
        """Inspect passive breaker registry and strategy without opening requests."""
        if self._circuit_breaker is None:
            return (
                DoctorCheck(
                    "circuit_breaker",
                    DoctorStatus.WARNING,
                    "No CircuitBreakerManager was supplied",
                ),
            )
        snapshots = self._circuit_breaker.list()
        states = {item.provider: item.state.value for item in snapshots}
        open_providers = [
            item.provider for item in snapshots if item.state is CircuitState.OPEN
        ]
        status = DoctorStatus.ERROR if open_providers else DoctorStatus.PASS
        message = (
            "One or more provider breakers are open"
            if open_providers
            else "Circuit breaker registry and strategy are available"
        )
        return (
            DoctorCheck(
                "circuit_breaker.registry",
                status,
                message,
                {
                    "provider_count": len(snapshots),
                    "states": states,
                    "open_providers": open_providers,
                    "strategy": type(self._circuit_breaker.strategy).__name__,
                },
            ),
        )

    def _routing_checks(self) -> tuple[DoctorCheck, ...]:
        """Inspect routing metadata and passive integrations without provider calls."""
        if self._routing is None:
            return (
                DoctorCheck(
                    "routing",
                    DoctorStatus.WARNING,
                    "No RoutingManager was supplied",
                ),
            )
        metadata = self._routing.list()
        integration = {
            "strategy": type(self._routing.strategy).__name__,
            "health_integration": self._routing.router.health_registry is not None,
            "breaker_integration": self._routing.router.breaker_registry is not None,
        }
        if not metadata:
            return (
                DoctorCheck(
                    "routing.registry",
                    DoctorStatus.WARNING,
                    "No provider routing metadata is registered",
                    integration,
                ),
            )
        decision = self._routing.route()
        status = (
            DoctorStatus.PASS if decision.selected_provider else DoctorStatus.WARNING
        )
        return (
            DoctorCheck(
                "routing.registry",
                status,
                (
                    "Routing metadata and passive integrations are available"
                    if decision.selected_provider
                    else "No provider currently satisfies routing filters"
                ),
                {
                    **integration,
                    "provider_count": len(metadata),
                    "providers": [item.provider for item in metadata],
                    "current_decision": decision.selected_provider,
                },
            ),
        )

    def _load_checks(self) -> tuple[DoctorCheck, ...]:
        """Inspect passive load collection and optional routing strategy wiring."""
        if self._load is None:
            return (
                DoctorCheck(
                    "load",
                    DoctorStatus.WARNING,
                    "No LoadManager was supplied",
                ),
            )
        snapshots = self._load.list()
        high = [
            item.provider
            for item in snapshots
            if item.status in {LoadStatus.HIGH, LoadStatus.SATURATED}
        ]
        unknown = [
            item.provider for item in snapshots if item.status is LoadStatus.UNKNOWN
        ]
        saturated = [
            item.provider for item in snapshots if item.status is LoadStatus.SATURATED
        ]
        strategy_attached = (
            self._routing is not None
            and isinstance(self._routing.strategy, LoadAwareStrategy)
            and self._routing.strategy.load_registry is self._load.registry
        )
        if saturated:
            status = DoctorStatus.ERROR
            message = "One or more providers are locally saturated"
        elif high or unknown or not snapshots:
            status = DoctorStatus.WARNING
            message = "Load data is incomplete or has high local load"
        else:
            status = DoctorStatus.PASS
            message = "Passive load collection is healthy"
        return (
            DoctorCheck(
                "load.registry",
                status,
                message,
                {
                    "provider_count": len(snapshots),
                    "high_providers": high,
                    "saturated_providers": saturated,
                    "unknown_providers": unknown,
                    "collector": type(self._load.collector).__name__,
                    "evaluator": type(self._load.evaluator).__name__,
                    "event_bus_subscribed": self._load.collector.event_bus is not None,
                    "routing_strategy_integration": strategy_attached,
                },
            ),
        )

    def _rate_limit_checks(self) -> tuple[DoctorCheck, ...]:
        """Inspect local quotas, EventBus, strategy, and routing composition."""
        if self._rate_limit is None:
            return (
                DoctorCheck(
                    "rate_limit",
                    DoctorStatus.WARNING,
                    "No RateLimitManager was supplied",
                ),
            )
        snapshots = self._rate_limit.list()
        exhausted = [
            f"{item.provider}/{item.scope}"
            for item in snapshots
            if item.requests_per_minute and item.remaining_requests == 0
        ]
        routing_strategy = self._routing.strategy if self._routing is not None else None
        strategy_attached = (
            isinstance(routing_strategy, RateLimitAwareStrategy)
            and routing_strategy.registry is self._rate_limit.registry
            and routing_strategy.quota_strategy is self._rate_limit.strategy
        )
        if exhausted:
            status = DoctorStatus.WARNING
            message = "One or more local quotas are exhausted"
        elif not snapshots:
            status = DoctorStatus.WARNING
            message = "No provider quotas are registered"
        else:
            status = DoctorStatus.PASS
            message = "Local quota registry and strategy are available"
        return (
            DoctorCheck(
                "rate_limit.registry",
                status,
                message,
                {
                    "provider_quota_count": len(snapshots),
                    "exhausted_quotas": exhausted,
                    "strategy": type(self._rate_limit.strategy).__name__,
                    "event_bus_available": self._rate_limit.event_bus is not None,
                    "routing_strategy_integration": strategy_attached,
                },
            ),
        )

    def _cache_checks(self) -> tuple[DoctorCheck, ...]:
        """Inspect backend registry and local cache effectiveness without reads."""
        if self._cache is None:
            return (
                DoctorCheck(
                    "cache", DoctorStatus.WARNING, "No CacheManager was supplied"
                ),
            )
        summaries = self._cache.summary()
        if not summaries:
            return (
                DoctorCheck(
                    "cache.registry",
                    DoctorStatus.ERROR,
                    "No cache backends are registered",
                ),
            )
        return (
            DoctorCheck(
                "cache.registry",
                DoctorStatus.PASS,
                "Cache backend registry is available",
                {"backends": summaries, "backend_count": len(summaries)},
            ),
        )

    def _plugin_checks(self) -> tuple[DoctorCheck, ...]:
        """Inspect loaded plugin metadata and hooks without invoking plugins."""
        if self._plugins is None:
            return (
                DoctorCheck(
                    "plugins", DoctorStatus.WARNING, "No PluginManager was supplied"
                ),
            )
        names = self._plugins.names()
        enabled = [name for name in names if self._plugins.registry.enabled(name)]
        disabled = [name for name in names if name not in enabled]
        failed = [
            event.plugin
            for event in self._plugins.events
            if event.name == "PluginFailed"
        ]
        status = (
            DoctorStatus.ERROR
            if failed
            else (DoctorStatus.PASS if names else DoctorStatus.WARNING)
        )
        return (
            DoctorCheck(
                "plugins.registry",
                status,
                "Plugin registry is available" if names else "No plugins are loaded",
                {
                    "loaded": names,
                    "enabled": enabled,
                    "disabled": disabled,
                    "failed": failed,
                    "hook_count": len(names),
                },
            ),
        )

    @staticmethod
    def _unique_objects(values: Iterable[object]) -> tuple[object, ...]:
        """Deduplicate inspected objects by identity while preserving their order."""
        seen: set[int] = set()
        unique: list[object] = []
        for value in values:
            if id(value) not in seen:
                seen.add(id(value))
                unique.append(value)
        return tuple(unique)
