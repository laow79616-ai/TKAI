"""Immutable application version snapshots."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from applications.models import Application, utc_now


@dataclass(frozen=True)
class ApplicationVersion:
    application_id: str
    version: str
    snapshot: dict[str, Any]
    created_by: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "application_id": self.application_id,
            "version": self.version,
            "snapshot": self.snapshot,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }


class VersionStore:
    def __init__(self) -> None:
        self._items: dict[str, list[ApplicationVersion]] = defaultdict(list)

    def create(self, application: Application, actor: str) -> ApplicationVersion:
        if any(
            value.version == application.version
            for value in self._items[application.id]
        ):
            raise ValueError(f"Version already exists: {application.version}")
        value = ApplicationVersion(
            application.id, application.version, application.to_dict(), actor, utc_now()
        )
        self._items[application.id].append(value)
        return value

    def list(self, application_id: str | None = None) -> tuple[ApplicationVersion, ...]:
        if application_id is not None:
            return tuple(self._items[application_id])
        return tuple(value for values in self._items.values() for value in values)
