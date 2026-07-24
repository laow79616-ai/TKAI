from __future__ import annotations

from ..models import Deployment, DeploymentStatus
from .errors import DeploymentClosedError
from .factory import DeploymentFactory
from .lifecycle import DeploymentLifecycle
from .plan import DeploymentPlan, DeploymentValidation
from .registry import DeploymentRegistry


class ReferenceDeploymentService:
    def __init__(
        self,
        registry: DeploymentRegistry | None = None,
        factory: DeploymentFactory | None = None,
    ) -> None:
        self.registry = registry or DeploymentRegistry()
        self._factory = factory or DeploymentFactory()
        self._closed = False
        self._lifecycle = DeploymentLifecycle()

    def create(
        self, deployment_id: str, project_id: str, workspace_id: str, name: str
    ) -> Deployment:
        if self._closed:
            raise DeploymentClosedError("Reference deployment service is closed.")
        return self.registry.register(
            self._factory.create(deployment_id, project_id, workspace_id, name)
        )

    def get(self, deployment_id: str) -> Deployment:
        return self.registry.get(deployment_id)

    def list(self) -> tuple[Deployment, ...]:
        return self.registry.list()

    def plan(self, plan: DeploymentPlan) -> DeploymentPlan:
        return plan

    def validate(self, plan: DeploymentPlan) -> DeploymentValidation:
        return DeploymentValidation(True)

    def transition(self, deployment_id: str, target: DeploymentStatus) -> Deployment:
        item = self.get(deployment_id)
        event = self._lifecycle.transition(deployment_id, item.status, target)
        return Deployment(
            item.deployment_id,
            item.project_id,
            item.name,
            event.new_status,
            item.configuration,
            item.workspace_id,
            item.version,
            item.target,
            item.strategy,
            item.metadata,
            item.created_at,
            item.updated_at,
        )

    def snapshot(self) -> tuple[Deployment, ...]:
        return self.registry.snapshot()

    def close(self) -> None:
        self.registry.clear()
        self._closed = True
