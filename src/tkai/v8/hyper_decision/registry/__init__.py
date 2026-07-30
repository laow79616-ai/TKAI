"""Isolation-aware registries for immutable decision metadata."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from threading import RLock
from typing import Any, Generic, TypeVar

from tkai.v8.hyper_decision import contracts
from tkai.v8.hyper_decision.contracts import DecisionScope

RecordT = TypeVar("RecordT")


class DecisionRegistry(Generic[RecordT]):
    def __init__(self, name: str, identifier: Callable[[RecordT], str]) -> None:
        self.name = name
        self._identifier = identifier
        self._records: dict[tuple[str, str, str, str], RecordT] = {}
        self._lock = RLock()

    def register(self, record: RecordT) -> RecordT:
        scope = record.scope  # type: ignore[attr-defined]
        key = (
            scope.tenant,
            scope.workspace,
            scope.decision_namespace,
            self._identifier(record),
        )
        with self._lock:
            if key in self._records:
                raise ValueError(f"duplicate {self.name} metadata: {key[-1]}")
            self._records[key] = record
        return record

    def discover(self, scope: DecisionScope | None = None) -> tuple[RecordT, ...]:
        records: Iterable[RecordT] = self._records.values()
        if scope is not None:
            records = (
                x
                for x in records
                if x.scope.tenant == scope.tenant  # type: ignore[attr-defined]
                and x.scope.workspace == scope.workspace  # type: ignore[attr-defined]
                and scope.decision_namespace in {"*", x.scope.decision_namespace}  # type: ignore[attr-defined]
            )
        return tuple(sorted(records, key=self._identifier))

    def __len__(self) -> int:
        return len(self._records)


def _identifier(field: str) -> Callable[[Any], str]:
    return lambda item: str(getattr(item, field))


class DecisionRegistryCatalog:
    decisions: DecisionRegistry[contracts.DecisionMetadata]
    evidence: DecisionRegistry[contracts.EvidenceMetadata]

    def __init__(self) -> None:
        definitions = (
            ("profiles", contracts.DecisionProfile, "profile_id"),
            ("decisions", contracts.DecisionMetadata, "decision_id"),
            ("alternatives", contracts.AlternativeMetadata, "alternative_id"),
            ("comparisons", contracts.ComparisonMetadata, "comparison_id"),
            ("recommendations", contracts.RecommendationMetadata, "recommendation_id"),
            ("evaluations", contracts.EvaluationMetadata, "evaluation_id"),
            ("confidence", contracts.ConfidenceMetadata, "confidence_id"),
            ("evidence", contracts.EvidenceMetadata, "evidence_id"),
            ("reviews", contracts.ReviewMetadata, "review_id"),
            ("approvals", contracts.ApprovalMetadata, "approval_id"),
            ("compatibility", contracts.CompatibilityMetadata, "compatibility_id"),
        )
        for name, _record_type, identifier in definitions:
            setattr(
                self,
                name,
                DecisionRegistry(name, _identifier(identifier)),
            )


__all__ = ("DecisionRegistry", "DecisionRegistryCatalog")
