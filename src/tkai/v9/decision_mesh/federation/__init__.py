"""Bounded, local, reference-only decision federation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import cast

from tkai.v9.decision_mesh.contracts import Reference

ALLOWED_FRAMEWORKS = frozenset(
    {
        "v9_components",
        "v9_adaptive_meta_kernel",
        "v9_adaptive_intelligence_mesh",
        "v9_adaptive_governance_mesh",
        "v9_adaptive_knowledge_mesh",
        "v9_adaptive_reasoning_mesh",
        "v8_frameworks",
        "v7_frameworks",
        "v6_decision_centers",
        "v6_decision_evolution_center",
        "v6_intelligent_decision_center",
        "v6_business_intelligence_center",
    }
)


class ReadOnlyFederation:
    def __init__(self, maximum_sources: int = 128) -> None:
        if not 1 <= maximum_sources <= 1000:
            raise ValueError("maximum_sources must be between 1 and 1000")
        self.maximum_sources = maximum_sources
        self._references: tuple[Reference, ...] = ()

    def federate(
        self, sources: Iterable[Reference | Mapping[str, object]]
    ) -> tuple[Reference, ...]:
        values = tuple(
            item
            if isinstance(item, Reference)
            else Reference(
                identifier=str(item["identifier"]),
                version=str(item.get("version", "")),
                kind=str(item.get("kind", "metadata")),
                generation=str(item.get("generation", "")),
                framework=str(item.get("framework", "")),
                metadata=cast(Mapping[str, object], item.get("metadata", {})),
            )
            for item in sources
        )
        if len(values) > self.maximum_sources:
            raise ValueError("bounded source count exceeded")
        for value in values:
            if value.framework not in ALLOWED_FRAMEWORKS:
                raise ValueError(
                    f"source framework is not allowlisted: {value.framework}"
                )
            if value.metadata.get("remote") or value.metadata.get("network"):
                raise ValueError("remote discovery and network access are prohibited")
        self._references = values
        return self._references

    def references(self) -> tuple[Reference, ...]:
        return self._references

    @staticmethod
    def mutates_upstream() -> bool:
        return False


__all__ = ("ALLOWED_FRAMEWORKS", "ReadOnlyFederation")
