"""Deterministic read-only V6-V10 compatibility negotiation."""

from __future__ import annotations

SUPPORTED_GENERATIONS = frozenset({"v6", "v7", "v8", "v9", "v10"})
COMPATIBILITY_KINDS = (
    "contract",
    "interface",
    "schema",
    "capability",
    "framework",
    "module",
    "service",
    "configuration",
    "storage",
    "extension",
    "api",
    "openapi",
    "dashboard",
    "ai-studio",
    "runtime",
    "deployment",
    "integrity",
    "attestation",
)


def negotiate(
    source: str, target: str = "v10", *, kind: str = "framework"
) -> dict[str, object]:
    normalized_source, normalized_target = source.lower(), target.lower()
    compatible = (
        normalized_source in SUPPORTED_GENERATIONS
        and normalized_target == "v10"
        and kind in COMPATIBILITY_KINDS
    )
    return {
        "source": normalized_source,
        "target": normalized_target,
        "kind": kind,
        "compatible": compatible,
        "automatic_migration": False,
        "automatic_upgrade": False,
        "automatic_rollback": False,
        "read_only": True,
    }


__all__ = ("COMPATIBILITY_KINDS", "SUPPORTED_GENERATIONS", "negotiate")
