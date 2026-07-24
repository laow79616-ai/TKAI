"""Offline Cloud RC-2 failure, snapshot, lifecycle, and cleanup validation."""

from __future__ import annotations

import gc
import weakref

import pytest

from cloud.deployment import ReferenceDeploymentService
from cloud.deployment.errors import DeploymentNotFoundError
from cloud.execution import ExecutionStatus, ReferenceExecutionService
from cloud.execution.errors import ExecutionLifecycleError
from cloud.gateway import GatewayCapability, ReferencePlatformGateway
from cloud.project import ReferenceProjectService
from cloud.project.errors import ProjectNotFoundError
from cloud.storage import ReferenceStorageService
from cloud.storage.errors import StorageNotFoundError
from cloud.workspace import ReferenceWorkspaceService
from cloud.workspace.errors import WorkspaceNotFoundError


def test_cloud_reference_failures_are_local_and_independent() -> None:
    """A missing item or invalid transition does not corrupt other services."""
    workspace = ReferenceWorkspaceService()
    project = ReferenceProjectService()
    deployment = ReferenceDeploymentService()
    storage = ReferenceStorageService()
    execution = ReferenceExecutionService()
    workspace.create("workspace", "account", "Workspace")
    project.create("project", "workspace", "Project")
    deployment.create("deployment", "project", "workspace", "Deployment")
    storage.registry.register(
        storage.factory.storage("storage", "project", "workspace", "Storage")
    )
    execution.create("execution", "deployment", "project", "workspace")

    with pytest.raises(WorkspaceNotFoundError):
        workspace.workspace("missing")
    with pytest.raises(ProjectNotFoundError):
        project.project("missing")
    with pytest.raises(DeploymentNotFoundError):
        deployment.get("missing")
    with pytest.raises(StorageNotFoundError):
        storage.get("missing")
    with pytest.raises(ExecutionLifecycleError):
        execution.transition("execution", ExecutionStatus.COMPLETED)

    assert workspace.workspace("workspace").workspace_id == "workspace"
    assert project.project("project").project_id == "project"
    assert deployment.get("deployment").deployment_id == "deployment"
    assert storage.get("storage").storage_id == "storage"
    assert execution.get("execution").status is ExecutionStatus.QUEUED


def test_cloud_snapshots_are_stable_and_models_do_not_expose_metadata() -> None:
    """Reference snapshots are tuples and descriptor metadata remains read-only."""
    project = ReferenceProjectService()
    created = project.create(
        "project", "workspace", "Project", metadata={"key": "value"}
    )
    snapshot = project.registry.snapshot()
    assert isinstance(snapshot, tuple)
    with pytest.raises(TypeError):
        created.metadata["key"] = "changed"  # type: ignore[index]
    assert project.project("project").metadata == {"key": "value"}
    assert project.registry.snapshot() == snapshot


def test_cloud_lifecycle_cleanup_is_idempotent_and_releases_reference_state() -> None:
    """Repeated close clears local registries without workers or retained state."""
    service = ReferenceProjectService()
    service.create("project", "workspace", "Project")
    registry_ref = weakref.ref(service.registry)
    service.close()
    service.close()
    assert service.projects() == ()
    del service
    gc.collect()
    assert registry_ref() is None


def test_gateway_reference_failure_does_not_create_hidden_global_state() -> None:
    """Gateway instances retain only caller-supplied immutable capabilities."""
    first = ReferencePlatformGateway((GatewayCapability("cloud"),))
    second = ReferencePlatformGateway()
    assert first.capabilities() == (GatewayCapability("cloud"),)
    assert second.capabilities() == ()
    assert first.health().value == "healthy"
