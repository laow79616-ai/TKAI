"""
TKAI Template Manifest
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class TemplateManifest:
    name: str
    version: str
    author: str
    description: str = ""
    license: str = ""
    homepage: str = ""

    @classmethod
    def load(cls, template_dir: str | Path) -> TemplateManifest:
        template_dir = Path(template_dir)

        yaml_manifest = template_dir / "template.yaml"
        json_manifest = template_dir / "template.json"

        if yaml_manifest.exists():
            data = yaml.safe_load(yaml_manifest.read_text(encoding="utf-8"))
        elif json_manifest.exists():
            data = json.loads(json_manifest.read_text(encoding="utf-8"))
        else:
            raise FileNotFoundError(
                "Template manifest not found: "
                f"{yaml_manifest} or {json_manifest}"
            )

        if not isinstance(data, dict):
            raise ValueError("Template manifest must be a mapping")

        return cls(
            name=data["name"],
            version=data["version"],
            author=data.get("author", ""),
            description=data.get("description", ""),
            license=data.get("license", ""),
            homepage=data.get("homepage", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "license": self.license,
            "homepage": self.homepage,
        }
