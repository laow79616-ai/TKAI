"""Structural interfaces for resource framework adapters."""

from __future__ import annotations

from typing import Protocol

from ..contracts import Resource


class ResourceProvider(Protocol):
    def list(self) -> tuple[Resource, ...]: ...

    def get(self, resource_id: str) -> Resource: ...


__all__ = ("ResourceProvider",)
