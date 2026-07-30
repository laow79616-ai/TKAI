"""Normalization of legacy and current knowledge references."""

from __future__ import annotations

from collections.abc import Mapping

from tkai.v8.hyper_knowledge.contracts import KnowledgeReference


def normalize_reference(
    value: KnowledgeReference | Mapping[str, object], generation: str = ""
) -> KnowledgeReference:
    if isinstance(value, KnowledgeReference):
        return value
    identifier = value.get("identifier", value.get("id", ""))
    if not isinstance(identifier, str):
        raise TypeError("knowledge reference identifier must be a string")
    return KnowledgeReference(
        identifier=identifier,
        version=str(value.get("version", "")),
        uri=str(value.get("uri", "")),
        kind=str(value.get("kind", "knowledge")),
        generation=str(value.get("generation", generation)),
        framework=str(value.get("framework", "")),
        metadata={
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


__all__ = ("normalize_reference",)
