"""
TKAI Template Manifest
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
    def load(cls, template_dir: str | Path) -> "TemplateManifest":
        template_dir = Path(template_dir)

        manifest = template_dir / "template.yaml"

        if not manifest.exists():
            raise FileNotFoundError(
                f"Template manifest not found: {manifest}"
            )

        data = yaml.safe_load(
            manifest.read_text(encoding="utf-8")
        )

        return cls(**data)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "license": self.license,
            "homepage": self.homepage,
        }