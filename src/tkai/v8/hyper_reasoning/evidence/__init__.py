"""Reference-only evidence aggregation across TKAI generations."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from tkai.v8.hyper_reasoning.contracts import EvidenceRecord, ReasoningReference


def normalize_reference(
    value: ReasoningReference | Mapping[str, object],
    generation: str,
    framework: str = "",
) -> ReasoningReference:
    if isinstance(value, ReasoningReference):
        if value.generation not in {"", generation}:
            raise ValueError("reference generation does not match evidence source")
        return ReasoningReference(
            value.identifier,
            value.version,
            value.uri,
            value.kind,
            generation,
            value.framework or framework,
            value.metadata,
        )
    identifier = value.get("identifier", value.get("id", ""))
    if not isinstance(identifier, str):
        raise TypeError("reference identifier must be a string")
    return ReasoningReference(
        identifier,
        str(value.get("version", "")),
        str(value.get("uri", "")),
        str(value.get("kind", "metadata")),
        str(value.get("generation", generation)),
        str(value.get("framework", framework)),
        {
            str(key): item
            for key, item in value.items()
            if key
            not in {
                "identifier",
                "id",
                "version",
                "uri",
                "kind",
                "generation",
                "framework",
            }
        },
    )


class EvidenceAggregator:
    """Aggregates descriptors and never calls or mutates referenced systems."""

    SOURCE_NAMES = (
        "v8_hyper_knowledge",
        "v8_hyper_intelligence",
        "v8_frameworks",
        "v7_frameworks",
        "v6_ai_centers",
    )

    def aggregate(
        self,
        *,
        v8_hyper_knowledge: Iterable[ReasoningReference | Mapping[str, object]] = (),
        v8_hyper_intelligence: Iterable[ReasoningReference | Mapping[str, object]] = (),
        v8_frameworks: Iterable[ReasoningReference | Mapping[str, object]] = (),
        v7_frameworks: Iterable[ReasoningReference | Mapping[str, object]] = (),
        v6_ai_centers: Iterable[ReasoningReference | Mapping[str, object]] = (),
    ) -> dict[str, tuple[ReasoningReference, ...]]:
        sources = {
            "v8_hyper_knowledge": (v8_hyper_knowledge, "v8", "hyper-knowledge"),
            "v8_hyper_intelligence": (
                v8_hyper_intelligence,
                "v8",
                "hyper-intelligence",
            ),
            "v8_frameworks": (v8_frameworks, "v8", ""),
            "v7_frameworks": (v7_frameworks, "v7", ""),
            "v6_ai_centers": (v6_ai_centers, "v6", ""),
        }
        return {
            name: tuple(
                sorted(
                    (
                        normalize_reference(item, generation, framework)
                        for item in records
                    ),
                    key=lambda item: item.identifier,
                )
            )
            for name, (records, generation, framework) in sources.items()
        }

    @staticmethod
    def executes_actions() -> bool:
        return False

    @staticmethod
    def mutates_runtime_state() -> bool:
        return False


__all__ = ("EvidenceAggregator", "EvidenceRecord", "normalize_reference")
