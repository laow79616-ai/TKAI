"""Bounded, local, isolation-aware metadata registry."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Generic, TypeVar

from .models import MetadataProfile

T = TypeVar("T", bound=MetadataProfile)


class BoundedRegistry(Generic[T]):
    def __init__(self, *, maximum_items: int = 1024) -> None:
        if maximum_items < 1 or maximum_items > 10_000:
            raise ValueError("maximum_items must be between 1 and 10000")
        self._maximum_items = maximum_items
        self._items: dict[str, T] = {}

    def register(self, profile: T) -> T:
        if profile.id not in self._items and len(self._items) >= self._maximum_items:
            raise ValueError("registry capacity exceeded")
        self._items[profile.id] = profile
        return profile

    def get(
        self,
        item_id: str,
        *,
        tenant: str = "default",
        workspace: str = "default",
        namespace: str = "default",
    ) -> T:
        item = self._items[item_id]
        if item.isolation_key != (tenant, workspace, namespace):
            raise KeyError(item_id)
        return item

    def discover(
        self,
        *,
        tenant: str = "default",
        workspace: str = "default",
        namespace: str = "default",
        result_limit: int = 100,
    ) -> tuple[T, ...]:
        if result_limit < 0 or result_limit > 100:
            raise ValueError("result_limit must be between 0 and 100")
        scope = (tenant, workspace, namespace)
        matches = (item for item in self._items.values() if item.isolation_key == scope)
        return tuple(sorted(matches, key=lambda item: item.id))[:result_limit]

    def validate_references(self, known_ids: Iterable[str]) -> tuple[str, ...]:
        known = frozenset(known_ids)
        return tuple(
            sorted(
                {
                    reference
                    for item in self._items.values()
                    for reference in item.dependency_references
                    if reference not in known
                }
            )
        )

    def __len__(self) -> int:
        return len(self._items)
