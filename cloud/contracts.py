"""Cloud service Protocols for explicit future Platform adapters."""

from __future__ import annotations

from typing import Protocol

from .context import CloudContext
from .models import (
    Account,
    Deployment,
    Execution,
    Project,
    StorageDescriptor,
    Workspace,
)


class PlatformGateway(Protocol):
    """Explicit boundary through which Cloud may invoke Platform capabilities."""

    def execute(self, deployment: Deployment, context: CloudContext) -> Execution: ...


class CloudGateway(Protocol):
    """Future Cloud gateway boundary; no transport or endpoint is implemented."""

    def deployment(self, deployment_id: str, context: CloudContext) -> Deployment: ...
    def execute(self, deployment: Deployment, context: CloudContext) -> Execution: ...


class CloudAPI(Protocol):
    """Future REST/RPC-neutral Cloud API surface without a server implementation."""

    def list_workspaces(self, account_id: str) -> tuple[Workspace, ...]: ...
    def list_projects(self, workspace_id: str) -> tuple[Project, ...]: ...
    def list_deployments(self, project_id: str) -> tuple[Deployment, ...]: ...
    def list_executions(self, deployment_id: str) -> tuple[Execution, ...]: ...


class StorageService(Protocol):
    """Future storage declaration lookup boundary without storage access."""

    def storage_for(self, workspace_id: str) -> tuple[StorageDescriptor, ...]: ...


class BillingService(Protocol):
    """Reserved billing boundary; it does not calculate, charge, or invoice."""

    def account_for(self, account_id: str) -> Account: ...


class OrganizationService(Protocol):
    """Reserved organization boundary; it does not resolve Enterprise data."""

    def organization_for(self, account: Account) -> str | None: ...
