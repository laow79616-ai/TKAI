"""Thread-safe in-memory application catalog."""

from __future__ import annotations

from dataclasses import replace
from threading import RLock
from typing import Any
from uuid import uuid4

from applications.models import Application, ApplicationStatus, SharingScope, utc_now


class ApplicationCatalog:
    def __init__(self) -> None:
        self._items: dict[str, Application] = {}
        self._lock = RLock()

    def create(self, payload: dict[str, Any]) -> Application:
        required = ("name", "description", "owner", "category")
        missing = [key for key in required if not str(payload.get(key, "")).strip()]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        item = Application(
            id=str(payload.get("id") or uuid4()),
            name=str(payload["name"]),
            description=str(payload["description"]),
            version=str(payload.get("version", "0.1.0")),
            owner=str(payload["owner"]),
            category=str(payload["category"]),
            tags=tuple(map(str, payload.get("tags", ()))),
            agent=_optional(payload.get("agent")),
            workflow=_optional(payload.get("workflow")),
            plugins=tuple(map(str, payload.get("plugins", ()))),
            knowledge=tuple(map(str, payload.get("knowledge", ()))),
            model=_optional(payload.get("model")),
            metadata=dict(payload.get("metadata", {})),
        )
        with self._lock:
            if item.id in self._items:
                raise ValueError(f"Application already exists: {item.id}")
            self._items[item.id] = item
        return item

    def list(
        self, *, owner: str | None = None, category: str | None = None
    ) -> tuple[Application, ...]:
        with self._lock:
            values = tuple(self._items.values())
        return tuple(
            item
            for item in values
            if item.status is not ApplicationStatus.DELETED
            and (owner is None or item.owner == owner)
            and (category is None or item.category == category)
        )

    def get(self, application_id: str, *, include_deleted: bool = False) -> Application:
        with self._lock:
            item = self._items.get(application_id)
        if item is None or (
            item.status is ApplicationStatus.DELETED and not include_deleted
        ):
            raise KeyError(application_id)
        return item

    def replace(self, item: Application) -> Application:
        with self._lock:
            if item.id not in self._items:
                raise KeyError(item.id)
            self._items[item.id] = replace(item, updated_at=utc_now())
            return self._items[item.id]

    def update(self, application_id: str, payload: dict[str, Any]) -> Application:
        changes = {
            key: value
            for key, value in payload.items()
            if key not in {"id", "status", "created_at", "updated_at"}
        }
        for name in ("tags", "plugins", "knowledge"):
            if name in changes:
                changes[name] = tuple(map(str, changes[name]))
        if "sharing" in changes:
            changes["sharing"] = SharingScope(str(changes["sharing"]))
        return self.replace(replace(self.get(application_id), **changes))


def _optional(value: object) -> str | None:
    return None if value is None else str(value)
