"""Isolation-aware registries for immutable decision metadata."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from threading import RLock
from typing import Generic, Protocol, TypeVar, cast

from tkai.v9.decision_mesh.contracts import (
    Alternative,
    Approval,
    Comparison,
    Compatibility,
    Confidence,
    Context,
    Decision,
    DecisionScope,
    Evaluation,
    Profile,
    Recommendation,
    Review,
)


class ScopedRecord(Protocol):
    @property
    def scope(self) -> DecisionScope: ...


T = TypeVar("T", bound=ScopedRecord)


class Registry(Generic[T]):
    def __init__(self, name: str, identifier: Callable[[T], str]) -> None:
        self.name, self._identifier = name, identifier
        self._records: dict[tuple[str, str, str, str], T] = {}
        self._lock = RLock()

    def register(self, record: T) -> T:
        key = (
            record.scope.tenant, record.scope.workspace, record.scope.decision,
            self._identifier(record),
        )
        with self._lock:
            if key in self._records:
                raise ValueError(f"duplicate {self.name} record: {key[-1]}")
            self._records[key] = record
        return record

    def discover(
        self, scope: DecisionScope | None = None, limit: int = 100
    ) -> tuple[T, ...]:
        if not 0 <= limit <= 1000:
            raise ValueError("result limit must be between 0 and 1000")
        records: Iterable[T] = self._records.values()
        if scope:
            records = (
                item for item in records
                if item.scope.tenant == scope.tenant
                and item.scope.workspace == scope.workspace
                and scope.decision in {"*", item.scope.decision}
            )
        return tuple(sorted(records, key=self._identifier))[:limit]

    def __len__(self) -> int:
        return len(self._records)


class RegistryCatalog:
    profiles: Registry[Profile]
    contexts: Registry[Context]
    decisions: Registry[Decision]
    alternatives: Registry[Alternative]
    comparisons: Registry[Comparison]
    evaluations: Registry[Evaluation]
    recommendations: Registry[Recommendation]
    confidence: Registry[Confidence]
    reviews: Registry[Review]
    approvals: Registry[Approval]
    compatibility: Registry[Compatibility]

    def __init__(self) -> None:
        definitions = {
            "profiles": (Profile, "profile_id"), "contexts": (Context, "context_id"),
            "decisions": (Decision, "decision_id"),
            "alternatives": (Alternative, "alternative_id"),
            "comparisons": (Comparison, "comparison_id"),
            "evaluations": (Evaluation, "evaluation_id"),
            "recommendations": (Recommendation, "recommendation_id"),
            "confidence": (Confidence, "confidence_id"),
            "reviews": (Review, "review_id"), "approvals": (Approval, "approval_id"),
            "compatibility": (Compatibility, "compatibility_id"),
        }
        for name, (_, identifier) in definitions.items():
            def identify(item: ScopedRecord, key: str = identifier) -> str:
                return str(getattr(item, key))

            setattr(self, name, Registry(name, identify))

    def named(self) -> tuple[tuple[str, Registry[ScopedRecord]], ...]:
        names = (
            "profiles", "contexts", "decisions", "alternatives", "comparisons",
            "evaluations", "recommendations", "confidence", "reviews", "approvals",
            "compatibility",
        )
        return tuple(
            (name, cast(Registry[ScopedRecord], getattr(self, name))) for name in names
        )


__all__ = ("Registry", "RegistryCatalog", "ScopedRecord")
