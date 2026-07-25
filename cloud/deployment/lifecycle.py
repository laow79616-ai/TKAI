from __future__ import annotations

from dataclasses import dataclass

from ..models import DeploymentStatus
from .errors import DeploymentLifecycleError

_TRANSITIONS = {
    DeploymentStatus.DRAFT: {DeploymentStatus.PLANNED},
    DeploymentStatus.PLANNED: {DeploymentStatus.DEPLOYING},
    DeploymentStatus.DEPLOYING: {DeploymentStatus.ACTIVE, DeploymentStatus.FAILED},
    DeploymentStatus.ACTIVE: {
        DeploymentStatus.DEGRADED,
        DeploymentStatus.STOPPED,
        DeploymentStatus.ARCHIVED,
    },
    DeploymentStatus.DEGRADED: {DeploymentStatus.ACTIVE, DeploymentStatus.ARCHIVED},
    DeploymentStatus.STOPPED: {DeploymentStatus.ARCHIVED},
    DeploymentStatus.FAILED: {DeploymentStatus.PLANNED, DeploymentStatus.ARCHIVED},
}


@dataclass(frozen=True, slots=True)
class DeploymentLifecycleEvent:
    deployment_id: str
    old_status: DeploymentStatus
    new_status: DeploymentStatus


class DeploymentLifecycle:
    def transition(
        self, deployment_id: str, current: DeploymentStatus, target: DeploymentStatus
    ) -> DeploymentLifecycleEvent:
        if target not in _TRANSITIONS.get(current, set()):
            raise DeploymentLifecycleError(
                f"Illegal deployment transition: {current.value} -> {target.value}"
            )
        return DeploymentLifecycleEvent(deployment_id, current, target)
