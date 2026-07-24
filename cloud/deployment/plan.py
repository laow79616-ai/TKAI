from __future__ import annotations

from dataclasses import dataclass, field

from .errors import DeploymentPlanError


@dataclass(frozen=True, slots=True)
class DeploymentStep:
    step_id: str
    kind: str
    dependencies: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.step_id:
            raise DeploymentPlanError("Deployment step id is required.")
        object.__setattr__(self, "dependencies", tuple(self.dependencies))


@dataclass(frozen=True, slots=True)
class DeploymentValidation:
    valid: bool
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DeploymentPlan:
    deployment_id: str
    steps: tuple[DeploymentStep, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        steps = tuple(self.steps)
        ids = {step.step_id for step in steps}
        if len(ids) != len(steps):
            raise DeploymentPlanError("Deployment plan contains duplicate step ids.")
        if any(dep not in ids for step in steps for dep in step.dependencies):
            raise DeploymentPlanError("Deployment plan contains an unknown dependency.")
        if any(step.step_id in step.dependencies for step in steps):
            raise DeploymentPlanError("Deployment plan contains a simple cycle.")
        object.__setattr__(self, "steps", steps)
