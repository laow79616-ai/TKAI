"""Safe normalization for external metadata references."""

from __future__ import annotations

from collections.abc import Mapping

from tkai.v8.security import filter_secrets
from tkai.v9.knowledge_mesh.contracts import KnowledgeReference

MAX_METADATA_ITEMS = 128


def normalize_reference(
    value: KnowledgeReference | Mapping[str, object],
    *,
    default_generation: str = "",
) -> KnowledgeReference:
    """Normalize an immutable reference without dereferencing its URI."""

    if isinstance(value, KnowledgeReference):
        return value
    identifier = str(value.get("identifier", "")).strip()
    return KnowledgeReference(
        identifier=identifier,
        version=str(value.get("version", "")).strip(),
        uri=str(value.get("uri", "")).strip(),
        kind=str(value.get("kind", "metadata")).strip(),
        generation=str(value.get("generation", default_generation)).lower(),
        metadata=filter_secrets(value.get("metadata", {})),  # type: ignore[arg-type]
    )


def normalize_name(value: str) -> str:
    """Deterministically normalize a name without executing user code."""

    return " ".join(value.strip().split()).casefold()


def normalize_confidence(value: float) -> float:
    return min(1.0, max(0.0, float(value)))


__all__ = (
    "MAX_METADATA_ITEMS",
    "normalize_confidence",
    "normalize_name",
    "normalize_reference",
)
