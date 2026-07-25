"""Lightweight decorator registration for developer SDK extensions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from threading import RLock

from .errors import ExtensionRegistrationError


class ExtensionKind(str, Enum):
    """Supported extension categories for declarative auto-registration."""

    TOOL = "tool"
    PROVIDER = "provider"
    MEMORY = "memory"
    WORKFLOW = "workflow"


@dataclass(frozen=True, slots=True)
class Extension:
    """Immutable extension metadata and its original target."""

    name: str
    kind: ExtensionKind
    target: object


class ExtensionRegistry:
    """Thread-safe registry isolated from the V1.x plugin system."""

    def __init__(self) -> None:
        self._items: dict[tuple[ExtensionKind, str], Extension] = {}
        self._lock = RLock()

    def register(self, extension: Extension) -> Extension:
        """Register an extension once; duplicate kind/name pairs fail clearly."""
        key = (extension.kind, extension.name)
        with self._lock:
            if key in self._items:
                raise ExtensionRegistrationError(
                    f"Duplicate {extension.kind.value} extension: {extension.name}"
                )
            self._items[key] = extension
        return extension

    def list(self, kind: ExtensionKind | None = None) -> tuple[Extension, ...]:
        """Return registrations in stable kind/name order."""
        with self._lock:
            values = [
                item
                for item in self._items.values()
                if kind is None or item.kind is kind
            ]
        return tuple(sorted(values, key=lambda item: (item.kind.value, item.name)))

    def clear(self) -> None:
        """Clear registrations for explicit application lifecycle cleanup."""
        with self._lock:
            self._items.clear()


registry = ExtensionRegistry()


def _register(
    kind: ExtensionKind, name: str | None = None
) -> Callable[[object], object]:
    """Create a decorator that registers its target on definition."""

    def decorate(target: object) -> object:
        candidate = name or getattr(target, "__name__", type(target).__name__)
        extension_name = (
            candidate if isinstance(candidate, str) else type(target).__name__
        )
        registry.register(Extension(extension_name, kind, target))
        return target

    return decorate


def tool(
    target: object | None = None, *, name: str | None = None
) -> object | Callable[[object], object]:
    """Register a callable as an SDK tool."""
    decorator = _register(ExtensionKind.TOOL, name)
    return decorator if target is None else decorator(target)


def provider(
    target: object | None = None, *, name: str | None = None
) -> object | Callable[[object], object]:
    """Register a provider implementation declaratively."""
    decorator = _register(ExtensionKind.PROVIDER, name)
    return decorator if target is None else decorator(target)


def memory(
    target: object | None = None, *, name: str | None = None
) -> object | Callable[[object], object]:
    """Register a memory implementation declaratively."""
    decorator = _register(ExtensionKind.MEMORY, name)
    return decorator if target is None else decorator(target)


def workflow(
    target: object | None = None, *, name: str | None = None
) -> object | Callable[[object], object]:
    """Register a workflow declaration or factory declaratively."""
    decorator = _register(ExtensionKind.WORKFLOW, name)
    return decorator if target is None else decorator(target)
