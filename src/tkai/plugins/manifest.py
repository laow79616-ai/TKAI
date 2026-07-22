"""Plugin manifest parsing for the TKAI plugin framework."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tkai.core.exceptions import PluginError


@dataclass(frozen=True, slots=True)
class PluginManifest:
    """Metadata required to discover and load a plugin."""

    name: str
    version: str
    entry: str
    description: str = ""
    enabled: bool = True

    @classmethod
    def load(cls, plugin_dir: str | Path) -> PluginManifest:
        """Load and validate ``plugin.json`` from ``plugin_dir``."""
        path = Path(plugin_dir) / "plugin.json"
        if not path.is_file():
            raise PluginError(f"Plugin manifest not found: {path}")

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise PluginError(f"Invalid plugin manifest: {path}") from exc

        if not isinstance(data, dict):
            raise PluginError("Plugin manifest must be a JSON object")
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PluginManifest:
        """Create a validated manifest from decoded JSON data."""
        required = ("name", "version", "entry")
        missing = [field for field in required if not data.get(field)]
        if missing:
            raise PluginError(f"Plugin manifest missing fields: {', '.join(missing)}")

        return cls(
            name=str(data["name"]),
            version=str(data["version"]),
            entry=str(data["entry"]),
            description=str(data.get("description", "")),
            enabled=bool(data.get("enabled", True)),
        )
