"""Cloud architecture tests remain offline and validate declarations only."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from cloud import (
    Account,
    CloudConfiguration,
    CloudContext,
    Deployment,
    DeploymentStatus,
    Execution,
    ExecutionStatus,
    Project,
    StorageDescriptor,
    Workspace,
)
from cloud.contracts import BillingService, CloudAPI, CloudGateway, OrganizationService


def test_cloud_models_describe_explicit_platform_scopes() -> None:
    """Cloud descriptors retain caller-owned hierarchy and stable statuses."""
    account = Account("account-1", "Account", metadata={"tier": "reference"})
    workspace = Workspace("workspace-1", account.account_id, "Workspace")
    project = Project("project-1", workspace.workspace_id, "Project")
    deployment = Deployment(
        "deployment-1", project.project_id, "Deployment", DeploymentStatus.READY
    )
    execution = Execution(
        "execution-1", deployment.deployment_id, ExecutionStatus.PENDING
    )
    storage = StorageDescriptor("storage-1", workspace.workspace_id, "memory")

    assert deployment.status is DeploymentStatus.READY
    assert execution.status is ExecutionStatus.PENDING
    assert storage.workspace_id == workspace.workspace_id


def test_context_and_configuration_are_immutable_defensive_snapshots() -> None:
    """Cloud has neither global context nor mutable configuration input."""
    metadata = {"source": "test"}
    context = CloudContext(account_id="account-1", metadata=metadata)
    configuration = CloudConfiguration(metadata=metadata)
    metadata["source"] = "changed"

    assert context.to_dict()["metadata"] == {"source": "test"}
    assert dict(configuration.metadata) == {"source": "test"}
    with pytest.raises(FrozenInstanceError):
        context.account_id = "other"  # type: ignore[misc]


def test_cloud_contracts_are_import_only_protocol_boundaries() -> None:
    """Cloud API, gateway, billing, and organization contracts need no service."""
    assert CloudAPI.__name__ == "CloudAPI"
    assert CloudGateway.__name__ == "CloudGateway"
    assert BillingService.__name__ == "BillingService"
    assert OrganizationService.__name__ == "OrganizationService"


@pytest.mark.parametrize(
    "factory",
    (
        lambda: Account("", "Account"),
        lambda: Workspace("workspace", "", "Workspace"),
        lambda: Project("project", "", "Project"),
        lambda: Deployment("deployment", "", "Deployment"),
        lambda: Execution("execution", ""),
        lambda: StorageDescriptor("storage", "", "memory"),
    ),
)
def test_cloud_models_reject_missing_explicit_identifiers(factory: object) -> None:
    """Architecture declarations do not infer missing account or resource scope."""
    with pytest.raises(ValueError):
        factory()  # type: ignore[operator]
