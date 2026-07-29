"""Capability and module registries for the V7 kernel."""

from __future__ import annotations

from collections.abc import Iterable

from tkai.v7.contracts import Capability, Module, Version, VersionRange


class CapabilityRegistry:
    """Tracks capabilities without exposing module internals."""

    def __init__(self) -> None:
        self._capabilities: dict[str, dict[str, Capability]] = {}

    def register(self, capability: Capability) -> None:
        providers = self._capabilities.setdefault(capability.name, {})
        provider = capability.provider or "kernel"
        if provider in providers:
            raise ValueError(
                f"capability {capability.name!r} already provided by {provider!r}"
            )
        providers[provider] = capability

    def unregister_provider(self, provider: str) -> None:
        for name in tuple(self._capabilities):
            self._capabilities[name].pop(provider, None)
            if not self._capabilities[name]:
                del self._capabilities[name]

    def discover(
        self, name: str, versions: VersionRange | None = None
    ) -> tuple[Capability, ...]:
        matches = self._capabilities.get(name, {}).values()
        return tuple(
            sorted(
                (
                    capability
                    for capability in matches
                    if versions is None or versions.supports(capability.version)
                ),
                key=lambda item: (item.version, item.provider),
                reverse=True,
            )
        )

    def list(self) -> tuple[Capability, ...]:
        return tuple(
            capability
            for name in sorted(self._capabilities)
            for capability in self.discover(name)
        )


class ModuleRegistry:
    """Holds explicitly registered V7 modules."""

    def __init__(self, kernel_version: Version | None = None) -> None:
        self._kernel_version = kernel_version or Version(7)
        self._modules: dict[str, Module] = {}

    def register(self, module: Module) -> None:
        descriptor = module.descriptor
        if not descriptor.kernel_versions.supports(self._kernel_version):
            raise ValueError(
                f"module {descriptor.name!r} does not support kernel "
                f"{self._kernel_version}"
            )
        if descriptor.name in self._modules:
            raise ValueError(f"module {descriptor.name!r} already registered")
        self._modules[descriptor.name] = module

    def get(self, name: str) -> Module:
        try:
            return self._modules[name]
        except KeyError as error:
            raise LookupError(name) from error

    def list(self) -> tuple[Module, ...]:
        return tuple(self._modules[name] for name in sorted(self._modules))

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._modules))

    def extend(self, modules: Iterable[Module]) -> None:
        for module in modules:
            self.register(module)


__all__ = ("CapabilityRegistry", "ModuleRegistry")
