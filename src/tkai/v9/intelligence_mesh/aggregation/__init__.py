"""Reference-only aggregation across V6, V7, and V8."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from tkai.v9.intelligence_mesh.contracts import IntelligenceReference
from tkai.v9.intelligence_mesh.normalization import normalize_reference


class MetadataAggregator:
    """Aggregates descriptors only and never invokes referenced components."""

    SUPPORTED_GENERATIONS = frozenset({"v6", "v7", "v8", "v9"})

    def aggregate(
        self,
        generation: str,
        records: Iterable[IntelligenceReference | Mapping[str, object]],
    ) -> tuple[IntelligenceReference, ...]:
        normalized_generation = generation.lower()
        if normalized_generation not in self.SUPPORTED_GENERATIONS:
            raise ValueError(f"unsupported generation: {generation}")
        normalized = tuple(
            normalize_reference(item, default_generation=normalized_generation)
            for item in records
        )
        if any(
            item.generation not in {"", normalized_generation} for item in normalized
        ):
            raise ValueError("reference generation does not match aggregation source")
        return tuple(
            sorted(
                (
                    IntelligenceReference(
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
        v6_ai_centers: Iterable[IntelligenceReference | Mapping[str, object]] = (),
        v7_frameworks: Iterable[IntelligenceReference | Mapping[str, object]] = (),
        v8_frameworks: Iterable[IntelligenceReference | Mapping[str, object]] = (),
        v9_components: Iterable[IntelligenceReference | Mapping[str, object]] = (),
    ) -> dict[str, tuple[IntelligenceReference, ...]]:
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
