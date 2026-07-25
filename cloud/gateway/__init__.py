"""Explicit, offline adapters from Cloud descriptors to Platform boundaries."""

from .interfaces import (
    CloudGateway,
    DeploymentGateway,
    ExecutionGateway,
    PlatformGateway,
    ProjectGateway,
    StorageGateway,
    WorkspaceGateway,
)
from .models import GatewayCapability, GatewayHealth, GatewayVersion
from .reference import ReferencePlatformGateway

__all__ = (
    "CloudGateway",
    "DeploymentGateway",
    "ExecutionGateway",
    "GatewayCapability",
    "GatewayHealth",
    "GatewayVersion",
    "PlatformGateway",
    "ProjectGateway",
    "ReferencePlatformGateway",
    "StorageGateway",
    "WorkspaceGateway",
)
