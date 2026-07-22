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

from tkai.providers.http import AsyncHTTPTransport

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
    ) -> None:
        self.manager = manager
        self._transports = tuple(transports)
        self._runtimes = tuple(runtimes)
        self._adapters = tuple(adapters)
        self._bridges = tuple(bridges)
        self._fallback = fallback
        self._fallback_candidates = tuple(fallback_candidates)

    def run(self) -> DoctorReport:
        """Run every diagnostic once and return a complete immutable report."""
        checks = [*self._environment_checks(), *self._provider_checks()]
        checks.extend(self._configuration_checks())
        checks.extend(self._capability_checks())
        checks.extend(self._transport_checks())
        checks.extend(self._runtime_checks())
        checks.extend(self._fallback_checks())
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
