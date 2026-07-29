"""Adapters that expose V6 objects through V7 contracts."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from tkai.v7.contracts import ModuleDescriptor, Version, VersionRange


@dataclass
class V6LifecycleAdapter:
    """Adapts legacy activate/deactivate objects without modifying them."""

    legacy: Any
    name: str
    context_factory: Callable[[Mapping[str, object]], object] = dict
    _context: object = field(init=False, default=None, repr=False)

    @property
    def descriptor(self) -> ModuleDescriptor:
        return ModuleDescriptor(
            self.name,
            Version(6),
            kernel_versions=VersionRange(Version(7), Version(7, 99, 99)),
        )

    def initialize(self, context: Mapping[str, object]) -> None:
        self._context = self.context_factory(context)

    def start(self) -> None:
        activate = getattr(self.legacy, "activate", None)
        if callable(activate):
            activate(self._context)

    def stop(self) -> None:
        deactivate = getattr(self.legacy, "deactivate", None)
        if callable(deactivate):
            deactivate(self._context)


def adapt_v6_module(
    legacy: Any,
    *,
    name: str | None = None,
    context_factory: Callable[[Mapping[str, object]], object] = dict,
) -> V6LifecycleAdapter:
    """Create an opt-in V6 adapter; no legacy API is patched or replaced."""
    return V6LifecycleAdapter(
        legacy=legacy,
        name=name or type(legacy).__name__,
        context_factory=context_factory,
    )


__all__ = ("V6LifecycleAdapter", "adapt_v6_module")
