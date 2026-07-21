"""
TKAI Generator Base

Abstract base class for all generators.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from tkai.core.context import Context


class BaseGenerator(ABC):
    """Base class for all generators."""

    def __init__(
        self,
        context: Context,
        *,
        name: str | None = None,
    ) -> None:
        self.context = context
        self.name = name or self.__class__.__name__

    @property
    def workspace(self):
        return self.context.workspace

    @property
    def project(self):
        return self.context.project

    @property
    def settings(self):
        return self.context.settings

    @property
    def registry(self):
        return self.context.registry

    def exists(self, path: Path) -> bool:
        """Check whether a file exists."""
        return path.exists()

    def mkdir(self, path: Path) -> None:
        """Create directory recursively."""
        path.mkdir(parents=True, exist_ok=True)

    def write(
        self,
        path: Path,
        content: str,
        *,
        encoding: str = "utf-8",
    ) -> None:
        """Write text to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)

    def read(
        self,
        path: Path,
        *,
        encoding: str = "utf-8",
    ) -> str:
        """Read text from file."""
        return path.read_text(encoding=encoding)

    @abstractmethod
    def generate(self, **kwargs: Any) -> Any:
        """Generate project artifacts."""
        raise NotImplementedError