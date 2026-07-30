"""Thread-safe, isolation-aware metadata registries."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from threading import RLock
from typing import Generic, TypeVar

from tkai.v8.hyper_intelligence.contracts import (
    CompatibilityRecord,
    EvidenceRecord,
    HyperIntelligenceProfile,
    IntelligenceScope,
    KnowledgeRecord,
    ReasoningSummary,
    Recommendation,
    SignalRecord,
)

RecordT = TypeVar("RecordT")


class IntelligenceRegistryError(RuntimeError):
    """Registry contract violation."""


class IntelligenceRegistry(Generic[RecordT]):
    """Store immutable metadata records without runtime adapters."""

    def __init__(
        self,
        name: str,
        identifier: Callable[[RecordT], str],
        scope: Callable[[RecordT], IntelligenceScope],
    ) -> None:
        self.name = name
        self._identifier = identifier
        self._scope = scope
        self._records: dict[tuple[str, str, str, str], RecordT] = {}
        self._lock = RLock()

    def register(self, record: RecordT) -> RecordT:
        record_scope = self._scope(record)
        key = (
            record_scope.tenant,
            record_scope.workspace,
            record_scope.knowledge_namespace,
            self._identifier(record),
        )
        with self._lock:
            if key in self._records:
                raise IntelligenceRegistryError(
                    f"duplicate {self.name} record: {key[-1]}"
                )
            self._records[key] = record
        return record

    def discover(self, scope: IntelligenceScope | None = None) -> tuple[RecordT, ...]:
        records: Iterable[RecordT] = self._records.values()
        if scope is not None:
            records = (
                record
                for record in records
                if self._scope(record).tenant == scope.tenant
                and self._scope(record).workspace == scope.workspace
                and scope.knowledge_namespace
                in {"*", self._scope(record).knowledge_namespace}
            )
        return tuple(sorted(records, key=self._identifier))

    def __len__(self) -> int:
        return len(self._records)


class IntelligenceRegistryCatalog:
    """All metadata stores owned by the fabric."""

    def __init__(self) -> None:
        self.profiles: IntelligenceRegistry[HyperIntelligenceProfile] = (
            IntelligenceRegistry(
                "profiles", lambda item: item.profile_id, lambda item: item.scope
            )
        )
        self.knowledge: IntelligenceRegistry[KnowledgeRecord] = IntelligenceRegistry(
            "knowledge", lambda item: item.knowledge_id, lambda item: item.scope
        )
        self.evidence: IntelligenceRegistry[EvidenceRecord] = IntelligenceRegistry(
            "evidence", lambda item: item.evidence_id, lambda item: item.scope
        )
        self.signals: IntelligenceRegistry[SignalRecord] = IntelligenceRegistry(
            "signals", lambda item: item.signal_id, lambda item: item.scope
        )
        self.reasoning: IntelligenceRegistry[ReasoningSummary] = IntelligenceRegistry(
            "reasoning", lambda item: item.summary_id, lambda item: item.scope
        )
        self.recommendations: IntelligenceRegistry[Recommendation] = (
            IntelligenceRegistry(
                "recommendations",
                lambda item: item.recommendation_id,
                lambda item: item.scope,
            )
        )
        self.compatibility: IntelligenceRegistry[CompatibilityRecord] = (
            IntelligenceRegistry(
                "compatibility",
                lambda item: item.compatibility_id,
                lambda item: item.scope,
            )
        )


__all__ = (
    "IntelligenceRegistry",
    "IntelligenceRegistryCatalog",
    "IntelligenceRegistryError",
)
