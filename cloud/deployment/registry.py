from __future__ import annotations

from threading import RLock

from ..models import Deployment
from .errors import DeploymentConflictError, DeploymentNotFoundError


class DeploymentRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._items: dict[str, Deployment] = {}

    def register(self, item: Deployment) -> Deployment:
        with self._lock:
            if item.deployment_id in self._items:
                raise DeploymentConflictError(item.deployment_id)
            self._items[item.deployment_id] = item
            return item

    def unregister(self, deployment_id: str) -> Deployment:
        with self._lock:
            try:
                return self._items.pop(deployment_id)
            except KeyError as exc:
                raise DeploymentNotFoundError(deployment_id) from exc

    def get(self, deployment_id: str) -> Deployment:
        with self._lock:
            try:
                return self._items[deployment_id]
            except KeyError as exc:
                raise DeploymentNotFoundError(deployment_id) from exc

    def exists(self, deployment_id: str) -> bool:
        with self._lock:
            return deployment_id in self._items

    def list(self) -> tuple[Deployment, ...]:
        with self._lock:
            return tuple(item for _, item in sorted(self._items.items()))

    def list_by_project(self, project_id: str) -> tuple[Deployment, ...]:
        return tuple(item for item in self.list() if item.project_id == project_id)

    def snapshot(self) -> tuple[Deployment, ...]:
        return self.list()

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
