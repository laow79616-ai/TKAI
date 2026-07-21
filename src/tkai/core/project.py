"""
TKAI Core Project

Project domain model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Project:
    """Project domain model."""

    name: str
    root: Path

    version: str = "0.1.0"
    template: str | None = None
    author: str | None = None
    description: str | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def config_file(self) -> Path:
        """Return tkai project config path."""
        return self.root / "tkai.yml"

    @property
    def exists(self) -> bool:
        """Whether this project exists."""
        return self.config_file.exists()

    def validate(self) -> bool:
        """Validate project."""
        return (
            bool(self.name)
            and self.root.exists()
            and self.root.is_dir()
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize project."""
        return {
            "name": self.name,
            "root": str(self.root),
            "version": self.version,
            "template": self.template,
            "author": self.author,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        """Deserialize project."""

        created = data.get("created_at")

        if created:
            created = datetime.fromisoformat(created)

            # 兼容旧版本（没有 tzinfo 的 ISO 时间）
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
        else:
            created = datetime.now(UTC)

        return cls(
            name=data["name"],
            root=Path(data["root"]),
            version=data.get("version", "0.1.0"),
            template=data.get("template"),
            author=data.get("author"),
            description=data.get("description"),
            created_at=created,
            metadata=data.get("metadata", {}),
        )