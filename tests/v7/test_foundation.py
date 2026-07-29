from __future__ import annotations

import importlib
import io
from collections.abc import Mapping
from typing import Protocol
from unittest.mock import Mock

import pytest

import tkai
from tkai.v7 import Capability, Kernel, ModuleDescriptor, Version, VersionRange
from tkai.v7.compatibility import adapt_v6_module
from tkai.v7.configuration import ConfigurationError, ConfigurationSchema
from tkai.v7.contracts import LifecycleState, ServiceDescriptor
from tkai.v7.interfaces import (
    InterfaceContract,
    InterfaceNotFoundError,
    InterfaceRegistry,
)
from tkai.v7.migration import MigrationPlan, MigrationStep
from tkai.v7.observability import AuditRecord, StructuredLogger
from tkai.v7.registry import CapabilityRegistry, ModuleRegistry
from tkai.v7.runtime import LifecycleError, LifecycleManager
from tkai.v7.security import (
    AccessController,
    IsolationPolicy,
    Principal,
    filter_secrets,
)
from tkai.v7.services import ServiceContainer, ServiceNotFoundError


class Greeting(Protocol):
    def greet(self) -> str: ...


class GreetingService:
    def greet(self) -> str:
        return "hello"


class FakeModule:
    def __init__(self, name: str = "fake") -> None:
        self._descriptor = ModuleDescriptor(
            name,
            Version(7),
            capabilities=(Capability("test.read"),),
        )
        self.calls: list[str] = []

    @property
    def descriptor(self) -> ModuleDescriptor:
        return self._descriptor

    def initialize(self, context: Mapping[str, object]) -> None:
        assert "kernel" in context
        self.calls.append("initialize")

    def start(self) -> None:
        self.calls.append("start")

    def stop(self) -> None:
        self.calls.append("stop")


def test_architecture_packages_import_without_side_effects() -> None:
    packages = (
        "core",
        "kernel",
        "runtime",
        "contracts",
        "interfaces",
        "registry",
        "modules",
        "services",
        "events",
        "state",
        "context",
        "pipeline",
        "scheduler",
        "planner",
        "analytics",
        "observability",
        "security",
        "configuration",
        "storage",
        "compatibility",
        "migration",
        "dashboard",
        "api",
    )
    for package in packages:
        assert importlib.import_module(f"tkai.v7.{package}")
    assert tkai.__version__ == "6.0.0"


def test_kernel_registers_and_manages_module_lifecycle() -> None:
    kernel = Kernel()
    module = FakeModule()
    kernel.register_module(module)
    assert kernel.modules.names() == ("fake",)
    assert kernel.capabilities.discover("test.read")[0].provider == "fake"
    kernel.start()
    assert module.calls == ["initialize", "start"]
    kernel.stop()
    assert module.calls[-1] == "stop"


def test_lifecycle_rolls_back_started_components() -> None:
    first = Mock()
    failing = Mock()
    failing.start.side_effect = RuntimeError("boom")
    manager = LifecycleManager()
    manager.add(first)
    manager.add(failing)
    manager.initialize({})
    with pytest.raises(LifecycleError):
        manager.start()
    first.stop.assert_called_once_with()
    assert manager.state(first) is LifecycleState.STOPPED
    assert manager.state(failing) is LifecycleState.FAILED


def test_module_and_capability_registries_reject_conflicts() -> None:
    modules = ModuleRegistry()
    module = FakeModule()
    modules.register(module)
    with pytest.raises(ValueError):
        modules.register(module)
    capabilities = CapabilityRegistry()
    capabilities.register(Capability("read", provider="one"))
    with pytest.raises(ValueError):
        capabilities.register(Capability("read", provider="one"))


def test_interface_version_negotiation_selects_latest_compatible() -> None:
    interfaces = InterfaceRegistry()
    interfaces.register(InterfaceContract("greeting", Version(7), GreetingService))
    interfaces.register(InterfaceContract("greeting", Version(7, 1), GreetingService))
    selected = interfaces.negotiate("greeting", VersionRange(Version(7), Version(7)))
    assert selected.version == Version(7)
    with pytest.raises(InterfaceNotFoundError):
        interfaces.negotiate("missing")


def test_dependency_injection_and_service_discovery() -> None:
    services = ServiceContainer()
    descriptor = ServiceDescriptor(
        "greeting", GreetingService, Version(7), frozenset({"greet"})
    )
    services.register(descriptor, lambda resolver: GreetingService())
    assert services.resolve(GreetingService).greet() == "hello"
    assert services.resolve(GreetingService) is services.resolve(GreetingService)
    assert services.discover("greet") == (descriptor,)
    with pytest.raises(ServiceNotFoundError):
        services.resolve(str)


def test_v6_compatibility_adapter_only_delegates_lifecycle() -> None:
    legacy = Mock()
    adapter = adapt_v6_module(legacy, name="legacy")
    adapter.initialize({"value": 1})
    adapter.start()
    adapter.stop()
    legacy.activate.assert_called_once_with({"value": 1})
    legacy.deactivate.assert_called_once_with({"value": 1})
    assert adapter.descriptor.version == Version(6)


def test_observability_registration_and_structured_secret_filtering() -> None:
    kernel = Kernel()
    metric = Mock()
    trace = Mock()
    audit = Mock()
    kernel.observability.register_metric(metric)
    kernel.observability.register_trace(trace)
    kernel.observability.register_health("kernel", lambda: True)
    kernel.observability.register_audit(audit)
    assert kernel.observability.health["kernel"]()
    audit(AuditRecord("start", "operator", "allowed"))
    audit.assert_called_once()
    output = io.StringIO()
    logger = StructuredLogger(output, filter_secrets)
    logger.log("info", "safe", api_token="private", visible="yes")
    assert "private" not in output.getvalue()
    assert "[REDACTED]" in output.getvalue()


def test_security_is_deny_by_default_and_isolates_capabilities() -> None:
    principal = Principal("user", frozenset({"operator"}))
    access = AccessController({"operator": {"kernel.read"}})
    assert access.allowed(principal, "kernel.read")
    with pytest.raises(PermissionError):
        access.require(principal, "kernel.write")
    isolation = IsolationPolicy()
    isolation.grant("module", {"state.read"})
    isolation.require("module", "state.read")
    with pytest.raises(PermissionError):
        isolation.require("module", "state.write")


def test_configuration_validation_uses_safe_strict_defaults() -> None:
    schema = ConfigurationSchema(
        validators={"enabled": lambda value: isinstance(value, bool)},
        required=frozenset({"enabled"}),
    )
    assert schema.validate({"enabled": True}) == {"enabled": True}
    with pytest.raises(ConfigurationError):
        schema.validate({"enabled": "yes"})
    assert Kernel().configuration["default_authorization"] == "deny"


def test_migration_scaffolding_never_executes_automatically() -> None:
    plan = MigrationPlan((MigrationStep("inventory", "Inventory V6"),))
    assert not plan.automatic
    assert plan.steps[0].identifier == "inventory"
    with pytest.raises(RuntimeError, match="automatic migration is disabled"):
        plan.execute()
