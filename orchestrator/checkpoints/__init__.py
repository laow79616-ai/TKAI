"""Tenant-scoped execution checkpoints."""

from copy import deepcopy
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Checkpoint:
    id: str
    execution_id: str
    tenant: str
    step: int
    state: dict[str, Any]


class CheckpointStore:
    def __init__(self) -> None:
        self._items: dict[str, Checkpoint] = {}

    def save(self, checkpoint: Checkpoint) -> Checkpoint:
        stored = Checkpoint(
            checkpoint.id,
            checkpoint.execution_id,
            checkpoint.tenant,
            checkpoint.step,
            deepcopy(checkpoint.state),
        )
        self._items[stored.id] = stored
        return stored

    def get(self, checkpoint_id: str, tenant: str) -> Checkpoint:
        item = self._items[checkpoint_id]
        if item.tenant != tenant:
            raise PermissionError("Cross-tenant checkpoint access is denied.")
        return item

    def list(self, tenant: str) -> tuple[Checkpoint, ...]:
        return tuple(item for item in self._items.values() if item.tenant == tenant)
