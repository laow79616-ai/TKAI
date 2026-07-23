"""Explicit Studio application dependency composition without global singletons."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from itertools import count
from threading import RLock

from studio.config import StudioSettings

from .gateway import SDKStudioGateway
from .repositories import (
    InMemoryExecutionRepository,
    InMemoryProjectRepository,
    InMemoryWorkflowRepository,
)
from .services import (
    ExecutionService,
    HealthService,
    ProjectService,
    SystemService,
    WorkflowService,
)


def deterministic_id_factory() -> Callable[[str], str]:
    """Create a local deterministic id generator suitable for reference storage."""
    sequence = count(1)
    lock = RLock()

    def create(prefix: str) -> str:
        with lock:
            return f"{prefix}-{next(sequence)}"

    return create


@dataclass(slots=True)
class StudioDependencies:
    """All explicitly composed services and reference resources for one app host."""

    settings: StudioSettings
    sdk_gateway: SDKStudioGateway
    project_repository: InMemoryProjectRepository
    workflow_repository: InMemoryWorkflowRepository
    execution_repository: InMemoryExecutionRepository
    project_service: ProjectService
    workflow_service: WorkflowService
    execution_service: ExecutionService
    health_service: HealthService
    system_service: SystemService
    owns_gateway: bool = False
    _shutdown: bool = field(default=False, init=False, repr=False)

    @classmethod
    def create(
        cls,
        *,
        settings: StudioSettings | None = None,
        sdk_gateway: SDKStudioGateway | None = None,
        project_repository: InMemoryProjectRepository | None = None,
        workflow_repository: InMemoryWorkflowRepository | None = None,
        execution_repository: InMemoryExecutionRepository | None = None,
        id_factory: Callable[[str], str] | None = None,
        owns_gateway: bool = False,
    ) -> StudioDependencies:
        """Compose safe local defaults without constructing a provider or runtime."""
        selected_settings = settings or StudioSettings()
        selected_gateway = sdk_gateway or SDKStudioGateway()
        projects = project_repository or InMemoryProjectRepository()
        workflows = workflow_repository or InMemoryWorkflowRepository()
        executions = execution_repository or InMemoryExecutionRepository()
        create_id = id_factory or deterministic_id_factory()
        return cls(
            settings=selected_settings,
            sdk_gateway=selected_gateway,
            project_repository=projects,
            workflow_repository=workflows,
            execution_repository=executions,
            project_service=ProjectService(projects, id_factory=create_id),
            workflow_service=WorkflowService(workflows, projects),
            execution_service=ExecutionService(
                executions, workflows, selected_gateway, id_factory=create_id
            ),
            health_service=HealthService(
                selected_gateway,
                {
                    "projects": projects,
                    "workflows": workflows,
                    "executions": executions,
                },
            ),
            system_service=SystemService(selected_settings),
            owns_gateway=owns_gateway,
        )

    def shutdown(self) -> None:
        """Close only an explicitly owned gateway; the operation is idempotent."""
        if self._shutdown:
            return
        if self.owns_gateway:
            self.sdk_gateway.close()
        self._shutdown = True
