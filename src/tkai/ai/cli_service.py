"""Read-only service facade used by the AI command-line interface."""

from __future__ import annotations

import platform
from collections.abc import Iterable
from typing import Any

from tkai import __version__
from tkai.adaptive import AdaptiveRoutingManager
from tkai.cache import CacheManager
from tkai.circuit_breaker import CircuitBreakerManager
from tkai.configuration import ConfigurationManager
from tkai.credentials import CredentialManager
from tkai.distributed import DistributedCoordinator
from tkai.health import HealthManager
from tkai.load import LoadManager
from tkai.observability import (
    EventBus,
    EventDispatcher,
    LoggerAdapter,
    MetricsAdapter,
    TraceAdapter,
)
from tkai.plugins import PluginManager
from tkai.policy import PolicyManager
from tkai.rate_limit import RateLimitManager
from tkai.retry import RetryManager
from tkai.routing import RoutingManager
from tkai.telemetry import TelemetryManager

from .doctor import DoctorReport, DoctorService
from .fallback import FallbackCandidate, FallbackEngine, FallbackPolicy
from .manager import ProviderManager
from .models import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
)


class AICommandService:
    """Aggregate existing AI services for thin, provider-agnostic CLI commands."""

    def __init__(
        self,
        manager: ProviderManager | None = None,
        *,
        fallback: FallbackEngine | FallbackPolicy | None = None,
        fallback_candidates: Iterable[FallbackCandidate[object]] = (),
        credentials: CredentialManager | None = None,
        configuration: ConfigurationManager | None = None,
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
        policies: PolicyManager | None = None,
        retries: RetryManager | None = None,
        distributed: DistributedCoordinator | None = None,
        telemetry: TelemetryManager | None = None,
        adaptive: AdaptiveRoutingManager | None = None,
    ) -> None:
        self.manager = manager or ProviderManager()
        self.fallback = fallback or FallbackEngine()
        self.fallback_candidates = tuple(fallback_candidates)
        self.credentials = credentials
        self.configuration = configuration
        self.health = health
        self.observability_bus = observability_bus
        self.observability_dispatcher = observability_dispatcher
        self.metrics_adapter = metrics_adapter
        self.logger_adapter = logger_adapter
        self.trace_adapter = trace_adapter
        self.circuit_breaker = circuit_breaker
        self.routing = routing
        self.load = load
        self.rate_limit = rate_limit
        self.cache = cache
        self.plugins = plugins
        self.policies = policies
        self.retries = retries
        self.distributed = distributed
        self.telemetry = telemetry
        self.adaptive = adaptive

    def adaptive_summary(self) -> dict[str, object]:
        """Return safe local adaptive state without selecting a provider."""
        return (
            self.adaptive.snapshot()
            if self.adaptive is not None
            else {"enabled": False, "routers": [], "weights": {}, "statistics": []}
        )

    def telemetry_summary(self) -> dict[str, object]:
        if self.telemetry is not None:
            return self.telemetry.summary()
        return {"exporters": [], "metrics": 0, "traces": 0, "logs": 0}

    def distributed_summary(self) -> dict[str, object]:
        """Return local distributed metadata without starting or probing anything."""
        if self.distributed is None:
            return {
                "backend": "LocalBackend",
                "started": False,
                "healthy": False,
                "nodes": [],
                "heartbeat": None,
                "resources": [],
            }
        return self.distributed.summary()

    def retry_summary(self) -> list[dict[str, object]]:
        """Return retry policy metadata without executing any operation."""
        return self.retries.summary() if self.retries is not None else []

    def policy_summary(self) -> list[dict[str, object]]:
        """Return safe registered-policy metadata without executing policies."""
        return self.policies.summary() if self.policies is not None else []

    def plugins_summary(self) -> list[dict[str, object]]:
        """Return safe loaded plugin metadata and enabled state."""
        if self.plugins is None:
            return []
        return [
            {
                **self.plugins.registry.metadata(name).to_dict(),
                "enabled": self.plugins.registry.enabled(name),
            }
            for name in self.plugins.names()
        ]

    def cache_summary(self) -> list[dict[str, object]]:
        """Return safe local cache backend summaries without entry values."""
        return self.cache.summary() if self.cache is not None else []

    def rate_limit_summary(self) -> list[dict[str, object]]:
        """Return stable JSON-ready local quota snapshots without provider calls."""
        if self.rate_limit is None:
            return []
        return [snapshot.to_dict() for snapshot in self.rate_limit.list()]

    def load_summary(self) -> list[dict[str, object]]:
        """Return stable JSON-ready local load snapshots without provider calls."""
        if self.load is None:
            return []
        return [snapshot.to_dict() for snapshot in self.load.list()]

    def breaker_summary(self) -> list[dict[str, Any]]:
        """Return stable, safe circuit breaker snapshots for CLI rendering."""
        if self.circuit_breaker is None:
            return []
        return [snapshot.to_dict() for snapshot in self.circuit_breaker.list()]

    def routing_summary(self) -> dict[str, Any]:
        """Return routing metadata and a passive simulated current decision."""
        if self.routing is None:
            return {
                "registered_providers": [],
                "strategy": None,
                "metadata": [],
                "current_decision": None,
            }
        metadata = self.routing.list()
        decision = self.routing.route()
        return {
            "registered_providers": [item.provider for item in metadata],
            "strategy": type(self.routing.strategy).__name__,
            "metadata": [
                {
                    "provider": item.provider,
                    "priority": item.priority,
                    "weight": item.weight,
                    "prompt_cost_per_1k": item.prompt_cost_per_1k,
                    "completion_cost_per_1k": item.completion_cost_per_1k,
                    "capabilities": sorted(item.capabilities),
                    "tags": sorted(item.tags),
                }
                for item in metadata
            ],
            "current_decision": decision.to_dict(),
        }

    def observability_summary(self) -> dict[str, Any]:
        """Return safe EventBus, adapter, subscriber, and event metadata."""
        bus = self.observability_bus
        dispatcher = self.observability_dispatcher
        recent_events = []
        if bus is not None:
            recent_events = [
                {
                    "name": event.name,
                    "timestamp": event.timestamp.isoformat(),
                    "trace_id": event.trace_id,
                    "correlation_id": event.correlation_id,
                }
                for event in bus.events[-5:]
            ]
        return {
            "event_bus": {
                "available": bus is not None,
                "event_count": len(bus.events) if bus is not None else 0,
            },
            "subscribers": len(dispatcher.subscribers) if dispatcher else 0,
            "adapters": {
                "metrics": self.metrics_adapter is not None,
                "logger": self.logger_adapter is not None,
                "trace": self.trace_adapter is not None,
            },
            "recent_events": recent_events,
        }

    def health_summary(self) -> list[dict[str, Any]]:
        """Return passive health snapshots and their most recent event safely."""
        if self.health is None:
            return []
        events = self.health.collector.events
        return [
            {
                "provider": item.provider,
                "status": item.status.value,
                "requests": item.statistics.requests,
                "success": item.statistics.success,
                "failure": item.statistics.failure,
                "timeout": item.statistics.timeout,
                "consecutive_failures": item.consecutive_failures,
                "recent_event": next(
                    (
                        event.event
                        for event in reversed(events)
                        if event.provider == item.provider
                    ),
                    None,
                ),
            }
            for item in self.health.registry.list()
        ]

    def configuration_summary(self) -> dict[str, Any]:
        """Return immutable resolved configuration metadata without secrets."""
        if self.configuration is None:
            return {
                "source": "default",
                "overrides": [],
                "application": {},
                "runtime": {},
                "providers": {},
            }
        config = self.configuration.list()
        return {
            "source": config.source,
            "overrides": list(config.overrides),
            "application": config.get("application", {}),
            "runtime": config.get("runtime", {}),
            "providers": config.get("providers", config.get("provider", {})),
            "loaded_files": [
                item for item in config.overrides if item in {"workspace", "user"}
            ],
        }

    def credentials_summary(self) -> list[dict[str, object]]:
        """Return safe local credential metadata without API key values."""
        if self.credentials is None:
            return []
        return [
            {
                "provider": item.provider,
                "configured": True,
                "source": item.source,
                "masked": item.masked(),
            }
            for item in self.credentials.list()
        ]

    def doctor(self) -> DoctorReport:
        """Run the complete read-only diagnostic suite."""
        return self._doctor_service().run()

    def validate_config(self) -> DoctorReport:
        """Run only provider registry, configuration, and capability diagnostics."""
        return self._doctor_service().validate_config()

    def providers(self) -> list[dict[str, Any]]:
        """Return safe provider summaries from the manager's registry metadata."""
        aliases = self.manager.aliases()
        summaries: list[dict[str, Any]] = []
        for name in self.manager.names():
            capabilities = self.manager.registry.capabilities_for(name)
            model_capabilities = self.manager.model_capabilities(name)
            summaries.append(
                {
                    "provider": name,
                    "aliases": sorted(
                        alias for alias, target in aliases.items() if target == name
                    ),
                    "default": name == self.manager.default_provider,
                    "capabilities": sorted(
                        capability.value for capability in capabilities.supported()
                    ),
                    "model_count": len(model_capabilities),
                }
            )
        return summaries

    def provider(self, name: str) -> dict[str, Any]:
        """Return one provider summary while resolving registered aliases."""
        canonical_name = self.manager.registry.resolve(name)
        for item in self.providers():
            if item["provider"] == canonical_name:
                return item
        self.manager.get(name)
        raise AssertionError("registered provider summary was not found")

    def models(self, name: str | None = None) -> list[str]:
        """Return model identifiers from the selected manager-owned provider."""
        return [model.id for model in self.manager.get(name).list_models()]

    def chat(
        self, message: str, *, provider: str | None = None, model: str | None = None
    ) -> ChatResponse:
        """Route a compatibility chat request through the existing manager."""
        return self.manager.chat(
            ChatRequest((ChatMessage("user", message),), model), provider=provider
        )

    def embed(
        self, text: str, *, provider: str | None = None, model: str | None = None
    ) -> EmbeddingResponse:
        """Route a compatibility embedding request through the existing manager."""
        return self.manager.embed(EmbeddingRequest((text,), model), provider=provider)

    def capabilities(
        self, *, provider: str | None = None, model: str | None = None
    ) -> list[dict[str, Any]]:
        """Return provider defaults and exact model capability overrides."""
        names = (
            [self.manager.registry.resolve(provider)]
            if provider
            else self.manager.names()
        )
        result: list[dict[str, Any]] = []
        for name in names:
            self.manager.get(name)
            model_capabilities = self.manager.model_capabilities(name)
            if model is not None:
                capabilities = self.manager.registry.capabilities_for(name, model)
                result.append(
                    {
                        "provider": name,
                        "model": model,
                        "override": model in model_capabilities,
                        "capabilities": sorted(
                            capability.value for capability in capabilities.supported()
                        ),
                    }
                )
                continue
            defaults = self.manager.registry.capabilities_for(name)
            result.append(
                {
                    "provider": name,
                    "model": None,
                    "override": False,
                    "capabilities": sorted(
                        capability.value for capability in defaults.supported()
                    ),
                    "model_overrides": {
                        key: sorted(item.value for item in value.supported())
                        for key, value in model_capabilities.items()
                    },
                }
            )
        return result

    def fallback_summary(self) -> dict[str, Any]:
        """Return fallback policy and ordered candidate metadata without execution."""
        policy = self._fallback_policy()
        return {
            "max_attempts": policy.max_attempts,
            "retry_budget": policy.retry_budget,
            "blacklist": sorted(policy.blocked_providers),
            "candidate_order": [
                candidate.name for candidate in self.fallback_candidates
            ],
        }

    def version(self) -> dict[str, str]:
        """Return framework and local runtime version metadata."""
        return {
            "tkai_version": __version__,
            "python_version": platform.python_version(),
            "runtime_version": platform.python_implementation(),
        }

    def info(self) -> dict[str, Any]:
        """Return a framework-level read-only summary using existing services."""
        report = self.doctor()
        runtime_checks = [
            check.name for check in report.checks if check.name.startswith("runtime")
        ]
        transport_checks = [
            check.name for check in report.checks if check.name.startswith("transport")
        ]
        return {
            "registered_providers": self.manager.names(),
            "default_provider": self.manager.default_provider,
            "runtime_checks": runtime_checks,
            "transport_checks": transport_checks,
            "capabilities": self.capabilities(),
            "fallback": self.fallback_summary(),
        }

    def _doctor_service(self) -> DoctorService:
        """Create a stateless doctor facade over the existing service objects."""
        return DoctorService(
            self.manager,
            fallback=self.fallback,
            fallback_candidates=self.fallback_candidates,
            credentials=self.credentials,
            persistent_configuration=self.configuration,
            health=self.health,
            observability_bus=self.observability_bus,
            observability_dispatcher=self.observability_dispatcher,
            metrics_adapter=self.metrics_adapter,
            logger_adapter=self.logger_adapter,
            trace_adapter=self.trace_adapter,
            circuit_breaker=self.circuit_breaker,
            routing=self.routing,
            load=self.load,
            rate_limit=self.rate_limit,
            cache=self.cache,
            plugins=self.plugins,
            policies=self.policies,
            retries=self.retries,
            distributed=self.distributed,
            telemetry=self.telemetry,
            adaptive=self.adaptive,
        )

    def _fallback_policy(self) -> FallbackPolicy:
        """Expose an existing fallback policy without executing fallback work."""
        if isinstance(self.fallback, FallbackEngine):
            return self.fallback.policy
        return self.fallback
