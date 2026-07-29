"""Modular TKAI V7 kernel."""

from __future__ import annotations

from collections.abc import Mapping

from tkai.v7.configuration import SAFE_DEFAULTS
from tkai.v7.context import RuntimeContext
from tkai.v7.contracts import Capability, Extension, Module, Version
from tkai.v7.events import Event, EventBus
from tkai.v7.interfaces import InterfaceRegistry
from tkai.v7.observability import ObservabilityRegistry
from tkai.v7.registry import CapabilityRegistry, ModuleRegistry
from tkai.v7.runtime import LifecycleManager
from tkai.v7.security import IsolationPolicy
from tkai.v7.services import ServiceContainer


class Kernel:
    """Composition root for opt-in V7 modules and services."""

    VERSION = Version(7)

    def __init__(
        self,
        *,
        context: RuntimeContext | None = None,
        configuration: Mapping[str, object] | None = None,
    ) -> None:
        self.context = context or RuntimeContext()
        self.configuration = {**SAFE_DEFAULTS, **(configuration or {})}
        self.services = ServiceContainer()
        self.capabilities = CapabilityRegistry()
        self.modules = ModuleRegistry(self.VERSION)
        self.interfaces = InterfaceRegistry()
        self.events = EventBus()
        self.observability = ObservabilityRegistry()
        self.isolation = IsolationPolicy()
        self.lifecycle = LifecycleManager()

    def register_module(self, module: Module) -> None:
        """Register an isolated module and its declared capabilities."""
        self.modules.register(module)
        self.lifecycle.add(module)
        for capability in module.descriptor.capabilities:
            if capability.provider and capability.provider != module.descriptor.name:
                raise ValueError("module capability provider must match module name")
            self.capabilities.register(
                capability
                if capability.provider
                else Capability(
                    capability.name,
                    capability.version,
                    module.descriptor.name,
                    capability.metadata,
                )
            )
        self.isolation.grant(
            module.descriptor.name,
            (item.name for item in module.descriptor.capabilities),
        )
        self.events.publish(
            Event("kernel.module.registered", {"name": module.descriptor.name})
        )

    def load_extension(self, extension: Extension) -> None:
        """Apply an extension only after the caller explicitly loads it."""
        extension.register(self)

    def start(self) -> None:
        """Initialize and start registered modules in registration order."""
        values = {"kernel": self, **self.context.values}
        self.lifecycle.initialize(values)
        self.lifecycle.start()
        self.events.publish(Event("kernel.started"))

    def stop(self) -> None:
        """Stop registered modules in reverse registration order."""
        self.lifecycle.stop()
        self.events.publish(Event("kernel.stopped"))


__all__ = ("Kernel",)
