"""Safe normalization for external metadata references."""

from __future__ import annotations

from collections.abc import Mapping

from tkai.v8.security import filter_secrets
from tkai.v9.intelligence_mesh.contracts import IntelligenceReference


def normalize_reference(
    value: IntelligenceReference | Mapping[str, object],
    *,
    default_generation: str = "",
) -> IntelligenceReference:
    """Normalize an immutable reference without dereferencing its URI."""

    if isinstance(value, IntelligenceReference):
        return value
    identifier = str(value.get("identifier", "")).strip()
    return IntelligenceReference(
        identifier=identifier,
        version=str(value.get("version", "")).strip(),
        uri=str(value.get("uri", "")).strip(),
        kind=str(value.get("kind", "metadata")).strip(),
        generation=str(value.get("generation", default_generation)).lower(),
        metadata=filter_secrets(value.get("metadata", {})),  # type: ignore[arg-type]
    )


__all__ = ("normalize_reference",)
