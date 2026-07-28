"""Primitive, collection, reference, temporal, spatial, and computed properties."""

from typing import Any, Protocol


class ComputedProperty(Protocol):
    """Safe adapter interface; implementations are registered by trusted code."""

    def compute(self, entity_id: str, context: dict[str, Any]) -> Any: ...
