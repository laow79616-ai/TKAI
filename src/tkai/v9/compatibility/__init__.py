"""Deterministic, explainable compatibility and version negotiation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NegotiationResult:
    requested_version: str
    available_versions: tuple[str, ...]
    compatible_versions: tuple[str, ...]
    selected_reference: str | None
    fallback_reference: str | None
    conflict_metadata: tuple[str, ...]
    explanation_summary: str
    migration_applied: bool = False


def _version_key(version: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError as error:
        raise ValueError(f"invalid numeric version: {version}") from error


def negotiate_version(
    requested: str, available: tuple[str, ...], *, compatible_major: int | None = None
) -> NegotiationResult:
    ordered = tuple(sorted(set(available), key=_version_key, reverse=True))
    major = (
        compatible_major if compatible_major is not None else _version_key(requested)[0]
    )
    compatible = tuple(
        version for version in ordered if _version_key(version)[0] == major
    )
    selected = (
        requested
        if requested in compatible
        else (compatible[0] if compatible else None)
    )
    fallback = compatible[-1] if compatible and compatible[-1] != selected else None
    conflicts = () if selected else (f"no compatible major version {major}",)
    explanation = (
        f"selected {selected} deterministically from compatible major {major}"
        if selected
        else f"no compatible major version {major}"
    )
    return NegotiationResult(
        requested, ordered, compatible, selected, fallback, conflicts, explanation
    )


def negotiate_generations(source: str, target: str) -> dict[str, object]:
    supported = {("v6", "v7"), ("v7", "v8"), ("v8", "v9"), ("v6", "v9")}
    compatible = (source, target) in supported or source == target
    return {
        "source": source,
        "target": target,
        "compatible": compatible,
        "automatic_migration": False,
        "explanation": "declared read-only adapter path"
        if compatible
        else "no declared adapter path",
    }


__all__ = ("NegotiationResult", "negotiate_generations", "negotiate_version")
