"""Pure metadata synchronization planning."""

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID, uuid5

from tkai.v8.hyper_coordination.contracts import (
    CoordinationScope,
    Reference,
    SynchronizationRecord,
)

_SYNC_NAMESPACE = UUID("9391e420-4dca-4b23-a981-41f998eea2ba")


class MetadataSynchronizer:
    """Build advisory synchronization records without applying changes."""

    CATEGORIES = (
        "metadata",
        "lifecycle",
        "compatibility",
        "version",
        "diagnostics",
    )

    def plan(
        self,
        category: str,
        source: Reference,
        target: Reference,
        changes: Mapping[str, object] | None = None,
        scope: CoordinationScope | None = None,
    ) -> SynchronizationRecord:
        selected_scope = scope or CoordinationScope()
        identity = (
            f"{category}:{source.identifier}:{target.identifier}:{selected_scope}"
        )
        return SynchronizationRecord(
            synchronization_id=str(uuid5(_SYNC_NAMESPACE, identity)),
            category=category,
            source=source,
            target=target,
            changes=changes or {},
            scope=selected_scope,
        )

    @staticmethod
    def runtime_synchronization_enabled() -> bool:
        return False


__all__ = ("MetadataSynchronizer",)
