"""
Template Manager
"""

from __future__ import annotations

import builtins
import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from .manifest import TemplateManifest


class TemplateManager:
    """Discover, inspect, and validate JSON or YAML project templates."""

    REQUIRED_FIELDS = ("name", "description", "version")

    def __init__(
        self,
        root: str | Path | None = None,
    ) -> None:
        self.root = (
            Path(root)
            if root is not None
            else Path(__file__).resolve().parents[3] / "templates"
        )
        # Retained for callers of the old template-engine manager.
        self.templates_dir = self.root

    def exists(
        self,
        template: str,
    ) -> bool:
        return (self.root / template).is_dir()

    def list(self) -> list[str]:
        """Return template directory names in stable order."""
        if not self.root.exists():
            return []
        return sorted(
            [
                p.name
                for p in self.root.iterdir()
                if p.is_dir() and p.name != "__pycache__"
            ]
        )

    def manifest(
        self,
        template: str,
    ) -> TemplateManifest:
        return TemplateManifest.load(self.root / template)

    def list_templates(self) -> builtins.list[dict[str, Any]]:
        """Return manifest metadata, retaining the legacy method name."""
        templates: builtins.list[dict[str, Any]] = []
        for name in self.list():
            try:
                templates.append(self.get_template(name))
            except FileNotFoundError:
                templates.append({"name": name, "description": "No description"})
        return templates

    def get_template(self, name: str) -> dict[str, Any]:
        """Return raw metadata for one template."""
        path = self._manifest_path(self.root / name)
        if path is None:
            raise FileNotFoundError(f"Template '{name}' not found.")
        return self._read_metadata(path)

    def validate_template(self, name: str) -> dict[str, Any]:
        """Return validation results for one template without raising."""
        result: dict[str, Any] = {"name": name, "valid": True, "errors": []}
        path = self._manifest_path(self.root / name)
        if path is None:
            result["valid"] = False
            result["errors"].append("template.json not found")
            return result

        try:
            metadata = self._read_metadata(path)
        except (JSONDecodeError, ValueError, OSError) as exc:
            result["valid"] = False
            result["errors"].append(f"Invalid manifest: {exc}")
            return result

        for field in self.REQUIRED_FIELDS:
            if field not in metadata:
                result["valid"] = False
                result["errors"].append(f"Missing field: {field}")
        return result

    def validate_all(self) -> builtins.list[dict[str, Any]]:
        """Validate every template in the configured root."""
        return [self.validate_template(name) for name in self.list()]

    @staticmethod
    def _manifest_path(template_dir: Path) -> Path | None:
        for filename in ("template.json", "template.yaml"):
            path = template_dir / filename
            if path.is_file():
                return path
        return None

    @staticmethod
    def _read_metadata(path: Path) -> dict[str, Any]:
        if path.suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            data = TemplateManifest.load(path.parent).to_dict()
        if not isinstance(data, dict):
            raise ValueError("Template manifest must be a mapping")
        return data
