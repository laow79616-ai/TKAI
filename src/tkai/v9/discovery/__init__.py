"""Bounded local discovery over explicit registries."""

from tkai.v9.registry import BoundedRegistry


def discover(registry: BoundedRegistry, *, limit: int = 100):  # type: ignore[no-untyped-def]
    return registry.discover(limit=limit)


__all__ = ("discover",)
