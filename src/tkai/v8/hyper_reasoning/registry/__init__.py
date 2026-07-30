"""Isolation-aware registries for immutable reasoning metadata."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from threading import RLock
from typing import Generic, TypeVar

from tkai.v8.hyper_reasoning.contracts import (
    CompatibilityRecord,
    ConfidenceMetadata,
    EvaluationMetadata,
    EvidenceRecord,
    ExplanationSummary,
    KnowledgeReferenceRecord,
    ReasoningMetadata,
    ReasoningProfile,
    ReasoningScope,
    Recommendation,
)

RecordT = TypeVar("RecordT")


class ReasoningRegistry(Generic[RecordT]):
    def __init__(
        self,
        name: str,
        identifier: Callable[[RecordT], str],
        scope: Callable[[RecordT], ReasoningScope],
    ) -> None:
        self.name = name
        self._identifier = identifier
        self._scope = scope
        self._records: dict[tuple[str, str, str, str], RecordT] = {}
        self._lock = RLock()

    def register(self, record: RecordT) -> RecordT:
        scope = self._scope(record)
        key = (
            scope.tenant,
            scope.workspace,
            scope.reasoning_namespace,
            self._identifier(record),
        )
        with self._lock:
            if key in self._records:
                raise ValueError(f"duplicate {self.name} metadata: {key[-1]}")
            self._records[key] = record
        return record

    def discover(self, scope: ReasoningScope | None = None) -> tuple[RecordT, ...]:
        records: Iterable[RecordT] = self._records.values()
        if scope is not None:
            records = (
                record
                for record in records
                if self._scope(record).tenant == scope.tenant
                and self._scope(record).workspace == scope.workspace
                and scope.reasoning_namespace
                in {"*", self._scope(record).reasoning_namespace}
            )
        return tuple(sorted(records, key=self._identifier))

    def __len__(self) -> int:
        return len(self._records)


class ReasoningRegistryCatalog:
    def __init__(self) -> None:
        self.profiles: ReasoningRegistry[ReasoningProfile] = ReasoningRegistry(
            "profiles", lambda item: item.profile_id, lambda item: item.scope
        )
        self.reasoning: ReasoningRegistry[ReasoningMetadata] = ReasoningRegistry(
            "reasoning", lambda item: item.reasoning_id, lambda item: item.scope
        )
        self.evaluations: ReasoningRegistry[EvaluationMetadata] = ReasoningRegistry(
            "evaluations", lambda item: item.evaluation_id, lambda item: item.scope
        )
        self.confidence: ReasoningRegistry[ConfidenceMetadata] = ReasoningRegistry(
            "confidence", lambda item: item.confidence_id, lambda item: item.scope
        )
        self.evidence: ReasoningRegistry[EvidenceRecord] = ReasoningRegistry(
            "evidence", lambda item: item.evidence_id, lambda item: item.scope
        )
        self.knowledge: ReasoningRegistry[KnowledgeReferenceRecord] = ReasoningRegistry(
            "knowledge", lambda item: item.knowledge_id, lambda item: item.scope
        )
        self.recommendations: ReasoningRegistry[Recommendation] = ReasoningRegistry(
            "recommendations",
            lambda item: item.recommendation_id,
            lambda item: item.scope,
        )
        self.explanations: ReasoningRegistry[ExplanationSummary] = ReasoningRegistry(
            "explanations", lambda item: item.explanation_id, lambda item: item.scope
        )
        self.compatibility: ReasoningRegistry[CompatibilityRecord] = ReasoningRegistry(
            "compatibility",
            lambda item: item.compatibility_id,
            lambda item: item.scope,
        )


__all__ = ("ReasoningRegistry", "ReasoningRegistryCatalog")
