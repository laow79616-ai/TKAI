"""Tenant/workspace namespace catalog."""

from __future__ import annotations

from collections import defaultdict

from ..models import MemoryScope


class NamespaceRegistry:
    def __init__(self) -> None:
        self._names: dict[tuple[str, str], set[str]] = defaultdict(set)

    def register(self, scope: MemoryScope, namespace: str) -> None:
        if not namespace:
            raise ValueError("Namespace is required.")
        self._names[(scope.tenant, scope.workspace)].add(namespace)

    def list(self, scope: MemoryScope) -> tuple[str, ...]:
        return tuple(sorted(self._names[(scope.tenant, scope.workspace)]))
