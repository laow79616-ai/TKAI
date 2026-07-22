"""
Template Manager
"""

from __future__ import annotations

from pathlib import Path

from .manifest import TemplateManifest


class TemplateManager:
    def __init__(
        self,
        root: str | Path,
    ) -> None:
        self.root = Path(root)

    def exists(
        self,
        template: str,
    ) -> bool:
        return (
            self.root / template
        ).exists()

    def list(self) -> list[str]:
        return sorted(
            [
                p.name
                for p in self.root.iterdir()
                if p.is_dir()
            ]
        )

    def manifest(
        self,
        template: str,
    ) -> TemplateManifest:
        return TemplateManifest.load(
            self.root / template
        )