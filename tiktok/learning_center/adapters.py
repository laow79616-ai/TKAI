"""Bounded read-only adapters for completed TikTok modules."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from tiktok.registry import TIKTOK_MODULE_KEYS

from .models import HistoricalOutcome, LearningContext

INTEGRATION_MODULES = tuple(
    dict.fromkeys(
        (
            "intelligence_center",
            "governance_center",
            "strategy_center",
            "mission_engine",
            *TIKTOK_MODULE_KEYS,
            "customer_journey_center",
            "crm_center",
            "recovery_center",
            "local_runtime",
        )
    )
)


class ReadOnlyLearningPort(Protocol):
    def read_history(
        self, subject: str, context: LearningContext
    ) -> Sequence[HistoricalOutcome]: ...


class ReferenceOnlyLearningPort:
    """Offline-safe adapter with no execute, publish, or mutation surface."""

    def __init__(
        self,
        module: str,
        outcomes: Sequence[HistoricalOutcome] = (),
        service: object | None = None,
    ) -> None:
        self.module = module
        self._outcomes = tuple(outcomes)
        self.service = service

    def read_history(
        self, subject: str, context: LearningContext
    ) -> Sequence[HistoricalOutcome]:
        del context
        return tuple(item for item in self._outcomes if item.subject == subject)
