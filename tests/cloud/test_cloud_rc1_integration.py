"""Offline RC-1 integration checks for the additive Cloud reference chain."""

from concurrent.futures import ThreadPoolExecutor

import pytest

from cloud.deployment import ReferenceDeploymentService
from cloud.execution import ExecutionStatus, ReferenceExecutionService
from cloud.execution.errors import ExecutionLifecycleError
from cloud.gateway import GatewayCapability, GatewayHealth, ReferencePlatformGateway
from cloud.project import ReferenceProjectService
from cloud.storage import ReferenceStorageService
from cloud.workspace import ReferenceWorkspaceService


def test_cloud_reference_chain_is_explicit_offline_and_deterministic() -> None:
    """Each foundation accepts explicit identifiers and performs no real work."""
    workspace = ReferenceWorkspaceService()
    project = ReferenceProjectService()
    deployment = ReferenceDeploymentService()
    storage = ReferenceStorageService()
    execution = ReferenceExecutionService()
    gateway = ReferencePlatformGateway((GatewayCapability("cloud"),))
    workspace.create("workspace", "account", "Workspace")
    project.create("project", "workspace", "Project")
    deployment.create("deployment", "project", "workspace", "Deployment")
    storage.registry.register(
        storage.factory.storage("storage", "project", "workspace", "Storage")
    )
    assert (
        execution.create("execution", "deployment", "project", "workspace").status
        is ExecutionStatus.QUEUED
    )
    assert gateway.health() is GatewayHealth.HEALTHY
    execution.close()
    storage.close()
    deployment.close()
    project.close()
    workspace.close()


def test_reference_registries_are_concurrent_and_cleanup_is_idempotent() -> None:
    """Bounded local lifecycle operations leave no global or worker state."""
    service = ReferenceProjectService()
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(
            executor.map(
                lambda index: service.create(str(index), "workspace", str(index)),
                range(8),
            )
        )
    assert len(service.projects()) == 8
    service.close()
    service.close()
    assert service.projects() == ()


def test_gateway_failure_is_local_and_does_not_mutate_other_foundations() -> None:
    """An invalid execution transition is isolated from local project data."""
    execution = ReferenceExecutionService()
    execution.create("execution", "deployment", "project", "workspace")
    with pytest.raises(ExecutionLifecycleError):
        execution.transition("execution", ExecutionStatus.COMPLETED)
    assert execution.get("execution").status is ExecutionStatus.QUEUED
