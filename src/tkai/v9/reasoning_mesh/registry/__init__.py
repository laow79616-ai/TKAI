"""Isolation-aware immutable reasoning metadata registries."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from threading import RLock
from typing import Generic, Protocol, TypeVar

from tkai.v9.reasoning_mesh.contracts import (
    Alternative,
    Assumption,
    Comparison,
    Confidence,
    Constraint,
    Context,
    Evaluation,
    Evidence,
    Explanation,
    Hypothesis,
    KnowledgeRecord,
    Observation,
    Profile,
    ReasoningScope,
    ReasoningSession,
    Recommendation,
    Review,
    Signal,
    Source,
)


class ScopedRecord(Protocol):
    @property
    def scope(self) -> ReasoningScope: ...


T = TypeVar("T", bound=ScopedRecord)


class RegistryError(RuntimeError):
    pass


class Registry(Generic[T]):
    def __init__(self, name: str, identifier: Callable[[T], str]) -> None:
        self.name = name
        self._identifier = identifier
        self._records: dict[tuple[str, str, str, str, str, str], T] = {}
        self._lock = RLock()

    def register(self, record: T) -> T:
        scope = record.scope
        key = (
            scope.tenant,
            scope.workspace,
            scope.namespace,
            scope.profile,
            scope.context,
            self._identifier(record),
        )
        with self._lock:
            if key in self._records:
                raise RegistryError(f"duplicate {self.name} record: {key[-1]}")
            self._records[key] = record
        return record

    def discover(
        self, scope: ReasoningScope | None = None, limit: int = 100
    ) -> tuple[T, ...]:
        if limit < 0 or limit > 1000:
            raise ValueError("result limit must be between 0 and 1000")
        records: Iterable[T] = self._records.values()
        if scope:
            records = (record for record in records if _visible(record, scope))
        return tuple(sorted(records, key=self._identifier))[:limit]

    def __len__(self) -> int:
        return len(self._records)


def _visible(record: ScopedRecord, requested: ReasoningScope) -> bool:
    actual = record.scope
    return (
        actual.tenant == requested.tenant
        and actual.workspace == requested.workspace
        and requested.namespace in {"*", actual.namespace}
        and requested.profile in {"*", actual.profile}
        and requested.context in {"*", actual.context}
    )


class RegistryCatalog:
    profiles: Registry[Profile]
    contexts: Registry[Context]
    sources: Registry[Source]
    knowledge: Registry[KnowledgeRecord]
    evidence: Registry[Evidence]
    signals: Registry[Signal]
    observations: Registry[Observation]
    hypotheses: Registry[Hypothesis]
    assumptions: Registry[Assumption]
    constraints: Registry[Constraint]
    reasoning: Registry[ReasoningSession]
    alternatives: Registry[Alternative]
    comparisons: Registry[Comparison]
    evaluations: Registry[Evaluation]
    confidence: Registry[Confidence]
    recommendations: Registry[Recommendation]
    explanations: Registry[Explanation]
    reviews: Registry[Review]

    def __init__(self) -> None:
        definitions = {
            "profiles": (Profile, "profile_id"),
            "contexts": (Context, "context_id"),
            "sources": (Source, "source_id"),
            "knowledge": (KnowledgeRecord, "knowledge_reference"),
            "evidence": (Evidence, "evidence_id"),
            "signals": (Signal, "signal_id"),
            "observations": (Observation, "observation_id"),
            "hypotheses": (Hypothesis, "hypothesis_id"),
            "assumptions": (Assumption, "assumption_id"),
            "constraints": (Constraint, "constraint_id"),
            "reasoning": (ReasoningSession, "reasoning_session_id"),
            "alternatives": (Alternative, "alternative_id"),
            "comparisons": (Comparison, "comparison_id"),
            "evaluations": (Evaluation, "evaluation_id"),
            "confidence": (Confidence, "confidence_id"),
            "recommendations": (Recommendation, "recommendation_id"),
            "explanations": (Explanation, "explanation_id"),
            "reviews": (Review, "review_id"),
        }
        for name, (_, attribute) in definitions.items():

            def identifier(item: object, key: str = attribute) -> str:
                value = getattr(item, key)
                return value.identifier if key == "knowledge_reference" else str(value)

            setattr(self, name, Registry(name, identifier))

    def named(self) -> tuple[tuple[str, Registry[ScopedRecord]], ...]:
        return tuple(
            (name, getattr(self, name))
            for name in (
                "profiles",
                "contexts",
                "sources",
                "knowledge",
                "evidence",
                "signals",
                "observations",
                "hypotheses",
                "assumptions",
                "constraints",
                "reasoning",
                "alternatives",
                "comparisons",
                "evaluations",
                "confidence",
                "recommendations",
                "explanations",
                "reviews",
            )
        )


__all__ = ("Registry", "RegistryCatalog", "RegistryError")
