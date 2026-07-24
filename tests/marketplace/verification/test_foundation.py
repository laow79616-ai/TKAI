from dataclasses import FrozenInstanceError

import pytest

from marketplace.verification import (
    ReferenceTrustService,
    ReferenceVerificationService,
    TrustDecision,
    TrustLevel,
    TrustPolicy,
    VerificationRequest,
    VerificationStatus,
)


def test_verification_models_service_snapshot_close():
    service = ReferenceVerificationService()
    report = service.verify(VerificationRequest(object()))
    assert report.result.status is VerificationStatus.PASSED
    assert service.snapshot().statistics.passed == 1
    with pytest.raises(FrozenInstanceError):
        report.result.status = VerificationStatus.FAILED
    service.close()
    with pytest.raises(RuntimeError):
        service.verify(VerificationRequest(object()))


def test_trust_policy_reports_and_isolation():
    service = ReferenceTrustService(TrustPolicy(minimum=TrustLevel.VERIFIED))
    assert service.evaluate(TrustLevel.COMMUNITY).decision is TrustDecision.REVIEW
    assert ReferenceTrustService().snapshot().statistics.total == 0
