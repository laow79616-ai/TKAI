"""Offline lifecycle and failure-isolation validation for Enterprise foundations."""

import pytest

from enterprise.audit import ReferenceAuditService
from enterprise.audit.errors import AuditClosedError
from enterprise.license import Edition, LicenseEntitlement, ReferenceLicenseService
from enterprise.license.errors import LicenseNotFoundError


def test_enterprise_reference_failures_are_isolated_and_cleanup_is_idempotent() -> None:
    audit = ReferenceAuditService()
    audit.close()
    audit.close()
    with pytest.raises(AuditClosedError):
        audit.get("missing")
    licenses = ReferenceLicenseService(
        (LicenseEntitlement("license", Edition.COMMUNITY),)
    )
    with pytest.raises(LicenseNotFoundError):
        licenses.get("missing")
    assert licenses.get("license").edition is Edition.COMMUNITY
