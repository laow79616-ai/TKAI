"""Application deployment and scaling."""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from applications.models import Deployment, DeploymentStatus, utc_now
from applications.runtime import ApplicationMetrics


class DeploymentService:
    def __init__(self, metrics: ApplicationMetrics) -> None:
        self._items: dict[str, Deployment] = {}
        self.metrics = metrics

    def deploy(
        self,
        application_id: str,
        version: str,
        actor: str,
        *,
        environment: str = "production",
        replicas: int = 1,
        quota: int = 1000,
    ) -> Deployment:
        if replicas < 1 or quota < 1:
            raise ValueError("Replicas and quota must be positive.")
        value = Deployment(
            str(uuid4()),
            application_id,
            version,
            environment,
            replicas,
            quota,
            DeploymentStatus.RUNNING,
            actor,
        )
        self._items[value.id] = value
        self.metrics.increment("deployments_total")
        return value

    def list(self) -> tuple[Deployment, ...]:
        return tuple(self._items.values())

    def get(self, deployment_id: str) -> Deployment:
        try:
            return self._items[deployment_id]
        except KeyError as error:
            raise KeyError(deployment_id) from error

    def scale(self, deployment_id: str, replicas: int) -> Deployment:
        if replicas < 1:
            raise ValueError("Replicas must be positive.")
        value = replace(
            self.get(deployment_id), replicas=replicas, updated_at=utc_now()
        )
        self._items[deployment_id] = value
        return value

    def record_run(self, deployment_id: str, *, failed: bool = False) -> Deployment:
        current = self.get(deployment_id)
        value = replace(
            current,
            runs=current.runs + 1,
            failures=current.failures + int(failed),
            updated_at=utc_now(),
        )
        self._items[deployment_id] = value
        return value
