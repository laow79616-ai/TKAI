import pytest

from cloud.deployment import (
    DeploymentFactory,
    DeploymentPlan,
    DeploymentStep,
    ReferenceDeploymentService,
)
from cloud.deployment.errors import DeploymentLifecycleError, DeploymentPlanError
from cloud.models import DeploymentStatus


def test_reference_deployment_is_local_and_lifecycle_is_declared():
    service = ReferenceDeploymentService()
    item = service.create("d1", "p1", "w1", "name")
    assert item.workspace_id == "w1"
    assert (
        service.transition("d1", DeploymentStatus.PLANNED).status
        is DeploymentStatus.PLANNED
    )
    with pytest.raises(DeploymentLifecycleError):
        service.transition("d1", DeploymentStatus.ACTIVE)
    service.close()
    service.close()


def test_plan_rejects_duplicate_unknown_and_simple_cycle():
    with pytest.raises(DeploymentPlanError):
        DeploymentPlan(
            "d", (DeploymentStep("x", "prepare"), DeploymentStep("x", "deploy"))
        )
    with pytest.raises(DeploymentPlanError):
        DeploymentPlan("d", (DeploymentStep("x", "prepare", ("missing",)),))
    with pytest.raises(DeploymentPlanError):
        DeploymentPlan("d", (DeploymentStep("x", "prepare", ("x",)),))
    assert (
        DeploymentPlan("d", (DeploymentStep("x", "prepare"),)).steps[0].step_id == "x"
    )


def test_factory_uses_explicit_ids_without_deployment():
    assert (
        DeploymentFactory().create("d", "p", "w", "n").status is DeploymentStatus.DRAFT
    )
