"""Cross-generation reference aggregation for the knowledge fabric."""

from __future__ import annotations

from collections.abc import Mapping

from tkai.v8.hyper_knowledge.contracts import KnowledgeReference
from tkai.v8.hyper_knowledge.normalization import normalize_reference


class KnowledgeAggregator:
    SOURCE_NAMES = ("v6_ai_centers", "v7_frameworks", "v8_frameworks")

    def aggregate(
        self,
        *,
        v6_ai_centers: tuple[KnowledgeReference | Mapping[str, object], ...] = (),
        v7_frameworks: tuple[KnowledgeReference | Mapping[str, object], ...] = (),
        v8_frameworks: tuple[KnowledgeReference | Mapping[str, object], ...] = (),
    ) -> dict[str, tuple[KnowledgeReference, ...]]:
        return {
            "v6_ai_centers": tuple(
                normalize_reference(item, "v6") for item in v6_ai_centers
            ),
            "v7_frameworks": tuple(
                normalize_reference(item, "v7") for item in v7_frameworks
            ),
            "v8_frameworks": tuple(
                normalize_reference(item, "v8") for item in v8_frameworks
            ),
        }


__all__ = ("KnowledgeAggregator",)
