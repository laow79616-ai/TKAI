"""
TKAI Core Workspace

Workspace lifecycle and directory management.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from .constants import (
    CACHE_DIR,
    DEFAULT_CONFIG_DIR,
    LOG_DIR,
    OUTPUT_DIR,
    PLUGIN_DIR,
    PROJECT_MARKER,
    TEMPLATE_DIR,
    TEMP_DIR,
)


@dataclass(slots=True)
class Workspace:
    """Workspace manager."""

    root: Path

    directories: tuple[str, ...] = field(
        default=(
            PROJECT_MARKER,
            DEFAULT_CONFIG_DIR,
            CACHE_DIR,
            LOG_DIR,
            OUTPUT_DIR,
            TEMP_DIR,
            TEMPLATE_DIR,
            PLUGIN_DIR,
        )
    )

    def exists(self) -> bool:
        """Return whether the workspace exists."""
        return self.root.exists()

    def create(self) -> None:
        """Create workspace root."""
        self.root.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> None:
        """Initialize workspace structure."""
        self.create()

        for directory in self.directories:
            (self.root / directory).mkdir(parents=True, exist_ok=True)

    def ensure_dir(self, name: str) -> Path:
        """Ensure a directory exists."""
        path = self.root / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def resolve(self, *parts: str) -> Path:
        """Resolve path inside workspace."""
        return self.root.joinpath(*parts)

    def clean(self) -> None:
        """Remove cache/temp/output directories."""
        for name in (CACHE_DIR, TEMP_DIR, OUTPUT_DIR):
            path = self.root / name
            if path.exists():
                shutil.rmtree(path)

    def remove(self) -> None:
        """Delete the entire workspace."""
        if self.root.exists():
            shutil.rmtree(self.root)