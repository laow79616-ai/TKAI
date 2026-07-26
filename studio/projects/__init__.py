"""Enterprise Studio project lifecycle and portability."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from threading import RLock

from studio.metrics import StudioMetrics


@dataclass(frozen=True, slots=True)
class Project:
    project_id: str
    name: str
    description: str = ""
    archived: bool = False
    resources: Mapping[str, object] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectManager:
    """Manage projects without owning runtime or provider resources."""

    def __init__(
        self, id_factory: Callable[[str], str], metrics: StudioMetrics | None = None
    ) -> None:
        self._id_factory = id_factory
        self._metrics = metrics or StudioMetrics()
        self._items: dict[str, Project] = {}
        self._lock = RLock()

    def create(self, name: str, description: str = "") -> Project:
        if not name.strip():
            raise ValueError("Project name is required.")
        item = Project(self._id_factory("project"), name.strip(), description)
        with self._lock:
            self._items[item.project_id] = item
        self._metrics.increment("studio_projects")
        return item

    def get(self, project_id: str) -> Project:
        with self._lock:
            try:
                return self._items[project_id]
            except KeyError as error:
                raise KeyError(f"Project not found: {project_id}") from error

    def list(self, *, include_archived: bool = False) -> tuple[Project, ...]:
        with self._lock:
            items = (self._items[key] for key in sorted(self._items))
            return tuple(
                item for item in items if include_archived or not item.archived
            )

    def rename(self, project_id: str, name: str) -> Project:
        if not name.strip():
            raise ValueError("Project name is required.")
        return self._replace(project_id, name=name.strip())

    def archive(self, project_id: str, archived: bool = True) -> Project:
        return self._replace(project_id, archived=archived)

    def clone(self, project_id: str, name: str | None = None) -> Project:
        source = self.get(project_id)
        item = replace(
            source,
            project_id=self._id_factory("project"),
            name=name or f"{source.name} (copy)",
            archived=False,
            resources=deepcopy(dict(source.resources)),
            created_at=datetime.now(timezone.utc),
        )
        with self._lock:
            self._items[item.project_id] = item
        self._metrics.increment("studio_projects")
        return item

    def export_project(self, project_id: str) -> dict[str, object]:
        item = self.get(project_id)
        payload = asdict(item)
        payload["created_at"] = item.created_at.isoformat()
        return {"schema_version": "2.3", "project": payload}

    def import_project(self, bundle: Mapping[str, object]) -> Project:
        raw = bundle.get("project")
        if bundle.get("schema_version") != "2.3" or not isinstance(raw, Mapping):
            raise ValueError("Invalid Studio project bundle.")
        name = raw.get("name")
        resources = raw.get("resources", {})
        if not isinstance(name, str) or not isinstance(resources, Mapping):
            raise ValueError("Invalid Studio project bundle.")
        item = self.create(name, str(raw.get("description", "")))
        return self._replace(item.project_id, resources=deepcopy(dict(resources)))

    def _replace(self, project_id: str, **changes: object) -> Project:
        with self._lock:
            updated = replace(self.get(project_id), **changes)
            self._items[project_id] = updated
            return updated


__all__ = ("Project", "ProjectManager")
