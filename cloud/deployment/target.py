from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum

from ..models import CloudValue, snapshot


class DeploymentTargetKind(str, Enum):
    LOCAL = "local"
    CONTAINER = "container"
    KUBERNETES = "kubernetes"
    SERVERLESS = "serverless"
    VIRTUAL_MACHINE = "virtual_machine"
    MANAGED_CLOUD = "managed_cloud"
    EXTERNAL = "external"


class DeploymentStrategyKind(str, Enum):
    RECREATE = "recreate"
    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    MANUAL = "manual"


@dataclass(frozen=True, slots=True)
class DeploymentCapability:
    name: str
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class DeploymentTarget:
    kind: DeploymentTargetKind
    region: str | None = None
    cluster: str | None = None
    namespace: str | None = None
    runtime: str | None = None
    capabilities: tuple[DeploymentCapability, ...] = ()
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "capabilities", tuple(self.capabilities))
        object.__setattr__(self, "metadata", snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class DeploymentStrategy:
    kind: DeploymentStrategyKind = DeploymentStrategyKind.MANUAL
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", snapshot(self.metadata))
