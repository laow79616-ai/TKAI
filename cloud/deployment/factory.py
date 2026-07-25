from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timezone

from ..models import CloudValue, Deployment, DeploymentStatus


class DeploymentFactory:
    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def create(
        self,
        deployment_id: str,
        project_id: str,
        workspace_id: str,
        name: str,
        *,
        version: str = "1",
        status: DeploymentStatus = DeploymentStatus.DRAFT,
        target: str | None = None,
        strategy: str = "manual",
        configuration: Mapping[str, CloudValue] | None = None,
        metadata: Mapping[str, CloudValue] | None = None,
    ) -> Deployment:
        now = self._clock()
        return Deployment(
            deployment_id,
            project_id,
            name,
            status,
            {} if configuration is None else configuration,
            workspace_id,
            version,
            target,
            strategy,
            {} if metadata is None else metadata,
            now,
            now,
        )
