"""Filesystem-based plugin discovery."""

from __future__ import annotations

from pathlib import Path

from tkai.core.exceptions import PluginError

from .manifest import PluginManifest


class PluginDiscovery:
    """Discover plugin manifests in a directory of plugin directories."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = (
            Path(root)
            if root is not None
            else Path(__file__).resolve().parents[3] / "plugins"
        )

    def discover(self) -> list[PluginManifest]:
        """Return valid manifests found directly below the configured root."""
        if not self.root.is_dir():
            return []

        manifests: list[PluginManifest] = []
        for directory in sorted(self.root.iterdir()):
            if not directory.is_dir() or directory.name == "__pycache__":
                continue
            manifest_path = directory / "plugin.json"
            if not manifest_path.exists():
                continue
            try:
                manifests.append(PluginManifest.load(directory))
            except PluginError as exc:
                raise PluginError(f"Failed to discover plugin: {directory}") from exc
        return manifests
