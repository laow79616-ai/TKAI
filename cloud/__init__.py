"""TKAI Cloud Platform 2.0 architecture contracts with no cloud integration."""

from .configuration import CloudConfiguration
from .context import CloudContext
from .contracts import (
    BillingService,
    CloudAPI,
    CloudGateway,
    OrganizationService,
    PlatformGateway,
)
from .models import (
    Account,
    Deployment,
    DeploymentStatus,
    Execution,
    ExecutionStatus,
    Project,
    ProjectStatus,
    StorageDescriptor,
    Workspace,
)

__all__ = (
    "Account",
    "BillingService",
    "CloudAPI",
    "CloudConfiguration",
    "CloudContext",
    "CloudGateway",
    "Deployment",
    "DeploymentStatus",
    "Execution",
    "ExecutionStatus",
    "OrganizationService",
    "PlatformGateway",
    "Project",
    "ProjectStatus",
    "StorageDescriptor",
    "Workspace",
)
