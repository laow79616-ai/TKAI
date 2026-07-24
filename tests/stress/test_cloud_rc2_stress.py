"""Bounded, offline concurrency checks for Cloud reference foundations."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from cloud.deployment import ReferenceDeploymentService
from cloud.execution import ReferenceExecutionService
from cloud.gateway import GatewayCapability, ReferencePlatformGateway
from cloud.project import ReferenceProjectService
from cloud.storage import ReferenceStorageService
from cloud.workspace import ReferenceWorkspaceService


def test_cloud_reference_registries_and_gateway_are_consistent_concurrently() -> None:
    """Concurrent local registration/read operations remain bounded and isolated."""
    workspace = ReferenceWorkspaceService()
    project = ReferenceProjectService()
    deployment = ReferenceDeploymentService()
    storage = ReferenceStorageService()
    execution = ReferenceExecutionService()
    gateway = ReferencePlatformGateway((GatewayCapability("cloud"),))

    def operate(index: int) -> tuple[str, str, str, str, str, str]:
        suffix = str(index)
        workspace.create(f"workspace-{suffix}", f"account-{suffix}", "Workspace")
        project.create(f"project-{suffix}", f"workspace-{suffix}", "Project")
        deployment.create(
            f"deployment-{suffix}",
            f"project-{suffix}",
            f"workspace-{suffix}",
            "Deployment",
        )
        storage.registry.register(
            storage.factory.storage(
                f"storage-{suffix}",
                f"project-{suffix}",
                f"workspace-{suffix}",
                "Storage",
            )
        )
        execution.create(
            f"execution-{suffix}",
            f"deployment-{suffix}",
            f"project-{suffix}",
            f"workspace-{suffix}",
        )
        return (
            workspace.workspace(f"workspace-{suffix}").workspace_id,
            project.project(f"project-{suffix}").project_id,
            deployment.get(f"deployment-{suffix}").deployment_id,
            storage.get(f"storage-{suffix}").storage_id,
            execution.get(f"execution-{suffix}").execution_id,
            gateway.health().value,
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(operate, range(32)))

    assert len(results) == 32
    assert len(workspace.workspaces()) == 32
    assert len(project.projects()) == 32
    assert len(deployment.snapshot()) == 32
    assert len(storage.snapshot()) == 32
    assert len(execution.snapshot()) == 32
    assert all(result[-1] == "healthy" for result in results)

    for service in (workspace, project, deployment, storage, execution):
        service.close()
