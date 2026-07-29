"""Explicit, non-automatic V7 migration planning."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MigrationStatus(str, Enum):
    """State of a migration step."""

    PENDING = "pending"
    COMPLETE = "complete"


@dataclass(frozen=True)
class MigrationStep:
    """A documented migration action; execution is deliberately external."""

    identifier: str
    description: str
    status: MigrationStatus = MigrationStatus.PENDING


class MigrationPlan:
    """Stores migration scaffolding and never executes steps."""

    def __init__(self, steps: tuple[MigrationStep, ...] = ()) -> None:
        self._steps = steps

    @property
    def steps(self) -> tuple[MigrationStep, ...]:
        return self._steps

    @property
    def automatic(self) -> bool:
        return False

    def execute(self) -> None:
        raise RuntimeError(
            "automatic migration is disabled; follow the documented migration plan"
        )


__all__ = ("MigrationPlan", "MigrationStatus", "MigrationStep")
