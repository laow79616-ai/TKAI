"""Bounded local reference-only federation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import cast

from tkai.v9.compatibility_mesh.contracts import Reference

ALLOWED_FRAMEWORKS = frozenset(
    {
        "v9_adaptive_meta_kernel",
        "v9_adaptive_intelligence_mesh",
        "v9_adaptive_governance_mesh",
        "v9_adaptive_knowledge_mesh",
        "v9_adaptive_reasoning_mesh",
        "v9_adaptive_decision_mesh",
        "v9_adaptive_planning_mesh",
        "v9_adaptive_operations_mesh",
        "v9_adaptive_recovery_mesh",
        "v9_components",
        "future_v9_components",
        "v8_frameworks",
        "v8_hyper_kernel",
        "v7_frameworks",
        "v7_capability_framework",
        "v7_configuration_framework",
        "v7_data_storage_framework",
        "v7_extension_framework",
        "v7_runtime_governance_framework",
        "v6_frameworks",
        "v6_runtime_manager",
        "v6_resource_center",
        "v6_risk_control_center",
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
            if value.generation and value.generation not in {"v6", "v7", "v8", "v9"}:
                raise ValueError(f"unsupported generation: {value.generation}")
            if value.framework not in ALLOWED_FRAMEWORKS:
                raise ValueError(
                    f"source framework is not allowlisted: {value.framework}"
                )
            if value.metadata.get("remote") or value.metadata.get("network"):
                raise ValueError("external network federation is prohibited")
        self._references = values
        return values

    def references(self) -> tuple[Reference, ...]:
        return self._references

    @staticmethod
    def mutates_upstream() -> bool:
        return False


__all__ = ("ALLOWED_FRAMEWORKS", "ReadOnlyFederation")
