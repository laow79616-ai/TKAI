"""Reference-only aggregation across V6, V7, and V8."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from tkai.v9.knowledge_mesh.contracts import KnowledgeReference
from tkai.v9.knowledge_mesh.normalization import normalize_reference


class MetadataAggregator:
    """Aggregates descriptors only and never invokes referenced components."""

    SUPPORTED_GENERATIONS = frozenset({"v6", "v7", "v8", "v9"})
    MAX_SOURCES_PER_GENERATION = 256

    def aggregate(
        self,
        generation: str,
        records: Iterable[KnowledgeReference | Mapping[str, object]],
    ) -> tuple[KnowledgeReference, ...]:
        normalized_generation = generation.lower()
        if normalized_generation not in self.SUPPORTED_GENERATIONS:
            raise ValueError(f"unsupported generation: {generation}")
        bounded_records = tuple(records)
        if len(bounded_records) > self.MAX_SOURCES_PER_GENERATION:
            raise ValueError("bounded source count exceeded")
        normalized = tuple(
            normalize_reference(item, default_generation=normalized_generation)
            for item in bounded_records
        )
        if any(
            item.generation not in {"", normalized_generation} for item in normalized
        ):
            raise ValueError("reference generation does not match aggregation source")
        return tuple(
            sorted(
                (
                    KnowledgeReference(
                        item.identifier,
                        item.version,
                        item.uri,
                        item.kind,
                        normalized_generation,
                        item.metadata,
                    )
                    for item in normalized
                ),
                key=lambda item: item.identifier,
            )
        )

    def aggregate_all(
        self,
        *,
        v6_ai_centers: Iterable[KnowledgeReference | Mapping[str, object]] = (),
        v7_frameworks: Iterable[KnowledgeReference | Mapping[str, object]] = (),
        v8_frameworks: Iterable[KnowledgeReference | Mapping[str, object]] = (),
        v9_components: Iterable[KnowledgeReference | Mapping[str, object]] = (),
    ) -> dict[str, tuple[KnowledgeReference, ...]]:
        return {
            "v6_ai_centers": self.aggregate("v6", v6_ai_centers),
            "v7_frameworks": self.aggregate("v7", v7_frameworks),
            "v8_frameworks": self.aggregate("v8", v8_frameworks),
            "v9_components": self.aggregate("v9", v9_components),
        }

    @staticmethod
    def executes_actions() -> bool:
        return False

    @staticmethod
    def mutates_runtime_state() -> bool:
        return False


__all__ = ("MetadataAggregator",)
