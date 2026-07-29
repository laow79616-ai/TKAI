"""Bounded, offline-safe, read-only adapters for approved knowledge sources."""

from __future__ import annotations

from typing import Protocol

from .models import KnowledgeContext

KNOWLEDGE_SOURCES = (
    "learning_center",
    "intelligence_center",
    "business_intelligence_center",
    "performance_insights",
    "analytics_center",
    "operations_planner",
    "strategy_center",
    "recovery_center",
    "decision_center",
)


class ReadOnlyKnowledgePort(Protocol):
    def read_knowledge(
        self, subject: str, context: KnowledgeContext
    ) -> dict[str, object]: ...


class ReferenceOnlyKnowledgePort:
    """Exposes one bounded read method and deliberately no mutation methods."""

    def __init__(self, source: str, service: object | None = None) -> None:
        if source not in KNOWLEDGE_SOURCES:
            raise ValueError(f"Unsupported knowledge source: {source}")
        self.source = source
        self.service = service

    def read_knowledge(
        self, subject: str, context: KnowledgeContext
    ) -> dict[str, object]:
        if not subject:
            raise ValueError("A bounded knowledge subject is required.")
        return {
            "source": self.source,
            "subject": subject,
            "tenant": context.tenant,
            "workspace": context.workspace,
            "summary": f"Read-only {self.source} knowledge for {subject}.",
            "confidence": 0.75,
            "integrity_reference": f"integrity://{self.source}/{subject}",
            "read_only": True,
            "runtime_configuration_modified": False,
            "publishing": False,
            "restriction_bypass": False,
        }
