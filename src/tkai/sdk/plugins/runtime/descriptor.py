"""Stable descriptors derived directly from immutable local plugin manifests."""

from __future__ import annotations

from dataclasses import dataclass

from .manifest import PluginManifest


@dataclass(frozen=True, slots=True)
class PluginDescriptor:
    """Public identity and capability summary for a registered local plugin."""

    name: str
    version: str
    capabilities: frozenset[str]

    @classmethod
    def from_manifest(cls, manifest: PluginManifest) -> PluginDescriptor:
        """Build an immutable descriptor without loading any entry point."""
        return cls(manifest.name, manifest.version, manifest.capabilities)
