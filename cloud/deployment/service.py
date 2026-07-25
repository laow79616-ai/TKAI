"""Deployment service protocol without execution semantics."""

from typing import Protocol

from ..models import Deployment


class DeploymentService(Protocol):
    def get(self, deployment_id: str) -> Deployment: ...
    def list(self) -> tuple[Deployment, ...]: ...
