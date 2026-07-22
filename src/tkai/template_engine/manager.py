"""Template discovery and backwards-compatible manifest validation."""

from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from tkai.templates.manager import TemplateManager as _TemplateCatalog
from tkai.templates.manifest import TemplateManifest


class TemplateManager(_TemplateCatalog):
    """Manage project templates stored in either JSON or YAML manifest format.

    The legacy ``list_templates``, ``get_template``, and validation methods are
    retained.  Newer callers may use ``list`` and ``manifest`` inherited from
    :class:`tkai.templates.manager.TemplateManager`.
    """

    REQUIRED_FIELDS = ("name", "description", "version")

    def __init__(self, root: str | Path | None = None) -> None:
        if root is None:
            root = Path(__file__).resolve().parents[3] / "templates"
        super().__init__(root)
        self.templates_dir = self.root

    def list_templates(self) -> list[dict[str, Any]]:
        """Return metadata for each available template.

        Directories without a manifest are represented with minimal metadata,
        preserving the behavior of the original implementation.
        """
        templates: list[dict[str, Any]] = []
        for name in self.list():
            try:
                templates.append(self.get_template(name))
            except FileNotFoundError:
                templates.append({"name": name, "description": "No description"})
        return templates

    def get_template(self, name: str) -> dict[str, Any]:
        """Return raw manifest metadata for one template."""
        directory = self.root / name
        manifest = self._manifest_path(directory)
        if manifest is None:
            raise FileNotFoundError(f"Template '{name}' not found.")
        return self._read_metadata(manifest)

    def validate_template(self, name: str) -> dict[str, Any]:
        """Validate one template manifest without raising on invalid metadata."""
        result: dict[str, Any] = {"name": name, "valid": True, "errors": []}
        manifest = self._manifest_path(self.root / name)
        if manifest is None:
            result["valid"] = False
            result["errors"].append("template.json not found")
            return result

        try:
            metadata = self._read_metadata(manifest)
        except (JSONDecodeError, ValueError) as exc:
            result["valid"] = False
            result["errors"].append(f"Invalid JSON: {exc}")
            return result
        except OSError as exc:
            result["valid"] = False
            result["errors"].append(str(exc))
            return result

        for field in self.REQUIRED_FIELDS:
            if field not in metadata:
                result["valid"] = False
                result["errors"].append(f"Missing field: {field}")
        return result

    def validate_all(self) -> list[dict[str, Any]]:
        """Validate every available template."""
        return [self.validate_template(name) for name in self.list()]

    @staticmethod
    def _manifest_path(template_dir: Path) -> Path | None:
        for name in ("template.json", "template.yaml"):
            candidate = template_dir / name
            if candidate.is_file():
                return candidate
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
