"""Bounded read-only adapters for completed TikTok modules."""

from __future__ import annotations

from typing import Protocol

from tiktok.registry import TIKTOK_MODULE_KEYS

from .models import IntelligenceContext

INTEGRATION_MODULES = tuple(
    dict.fromkeys(
        (
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


class ReadOnlyIntelligencePort(Protocol):
    def read_snapshot(
        self, subject: str, context: IntelligenceContext
    ) -> dict[str, object]: ...


class ReferenceOnlyIntelligencePort:
    """Offline-safe adapter exposing no execute, publish, or mutation method."""

    def __init__(self, module: str, service: object | None = None) -> None:
        self.module = module
        self.service = service

    def read_snapshot(
        self, subject: str, context: IntelligenceContext
    ) -> dict[str, object]:
        return {
            "module": self.module,
            "subject": subject,
            "tenant": context.tenant,
            "workspace": context.workspace,
            "available": True,
            "read_only": True,
            "restriction_bypass": False,
        }
