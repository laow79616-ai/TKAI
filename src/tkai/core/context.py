"""
TKAI Core Context

Application runtime context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .registry import Registry


@dataclass(slots=True)
class Context:
    """Runtime context container."""

    project: Any | None = None
    workspace: Any | None = None
    settings: Any | None = None
    registry: Registry = field(default_factory=Registry)

    logger: Any | None = None
    runtime: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, str] = field(default_factory=dict)
    services: dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        """Store a runtime object."""
        self.services[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a runtime object."""
        return self.services.get(key, default)

    def has(self, key: str) -> bool:
        """Return whether a runtime object exists."""
        return key in self.services

    def remove(self, key: str) -> Any:
        """Remove a runtime object."""
        return self.services.pop(key, None)

    def clear(self) -> None:
        """Clear runtime services."""
        self.services.clear()
        self.runtime.clear()

    def inject(
        self,
        *,
        project: Any | None = None,
        workspace: Any | None = None,
        settings: Any | None = None,
        logger: Any | None = None,
    ) -> None:
        """Inject core dependencies."""

        if project is not None:
            self.project = project

        if workspace is not None:
            self.workspace = workspace

        if settings is not None:
            self.settings = settings

        if logger is not None:
            self.logger = logger