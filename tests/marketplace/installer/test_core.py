from dataclasses import FrozenInstanceError

import pytest

from marketplace.installer import (
    InstallationId,
    InstallationRequest,
    InstallationStatus,
    InstallationStepType,
    ReferenceInstallerService,
    ReferenceResolutionInstallationSource,
)
from marketplace.installer.errors import (
    InstallerClosedError,
    InstallerConflictError,
    InstallerStateError,
)
from marketplace.installer.lifecycle import InstallationLifecycle
from marketplace.models import PackageVersion
from marketplace.resolver import (
    DependencyCoordinate,
    DependencyGraph,
    ResolutionResult,
    ResolutionStatus,
)


def result():
    c = DependencyCoordinate("p", "a", PackageVersion(1))
    return ResolutionResult(
        ResolutionStatus.RESOLVED, (), (c,), (c,), DependencyGraph()
    )


def request():
    return InstallationRequest(InstallationId("i"), result())


def test_models_request_and_adapter():
    r = request()
    assert ReferenceResolutionInstallationSource(r.resolution_result).coordinates()
    with pytest.raises(FrozenInstanceError):
        r.installation_id = InstallationId("x")
    with pytest.raises(ValueError):
        InstallationRequest(
            InstallationId("x"),
            ResolutionResult(
                ResolutionStatus.UNRESOLVED, (), (), (), DependencyGraph()
            ),
        )


def test_lifecycle():
    lifecycle = InstallationLifecycle()
    assert (
        lifecycle.transition(InstallationStatus.PENDING, InstallationStatus.PLANNED)
        is InstallationStatus.PLANNED
    )
    with pytest.raises(InstallerStateError):
        lifecycle.transition(InstallationStatus.PENDING, InstallationStatus.SUCCEEDED)


def test_plan_store_service_snapshot_cancel_close():
    s = ReferenceInstallerService()
    p = s.plan(request())
    assert [x.type for x in p.steps] == [
        InstallationStepType.VALIDATE,
        InstallationStepType.PREPARE,
        InstallationStepType.INSTALL,
        InstallationStepType.FINALIZE,
    ]
    out = s.install(request())
    assert out.session.status is InstallationStatus.SUCCEEDED
    assert s.snapshot().installed_records
    with pytest.raises(InstallerConflictError):
        s.install(request())
    assert s.cancel("i").status is InstallationStatus.CANCELLED
    s.clear()
    assert not s.snapshot().sessions
    s.close()
    assert s.snapshot().closed
    with pytest.raises(InstallerClosedError):
        s.plan(request())
