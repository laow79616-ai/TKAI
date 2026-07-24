"""Offline tests for Enterprise License Foundation."""

from concurrent.futures import ThreadPoolExecutor

from enterprise.license import (
    Edition,
    FeatureDescriptor,
    LicenseCapability,
    LicenseEntitlement,
    LicenseGrant,
    LicenseLimit,
    LicenseValidationRequest,
    ReferenceLicenseService,
    ReferenceLicenseValidator,
)


def item(identifier: str = "license-1") -> LicenseEntitlement:
    return LicenseEntitlement(
        identifier,
        Edition.ENTERPRISE,
        (LicenseGrant("audit"),),
        (LicenseLimit("users", 10),),
    )


def test_edition_capability_entitlement_and_validation_are_offline() -> None:
    entitlement = item()
    assert entitlement.edition is Edition.ENTERPRISE
    assert LicenseCapability("audit").enabled
    assert FeatureDescriptor("audit").name == "audit"
    assert (
        ReferenceLicenseValidator()
        .validate(LicenseValidationRequest(entitlement))
        .valid
    )


def test_reference_service_snapshot_is_thread_safe_and_non_enforcing() -> None:
    service = ReferenceLicenseService((item(),))
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: service.get("license-1"), range(4)))
    assert all(result is item() for result in results) is False
    assert service.snapshot()[0].entitlement_id == "license-1"


def test_license_documentation_states_no_activation_or_enforcement() -> None:
    document = (
        __import__("pathlib").Path(__file__).parents[3] / "docs" / "License.md"
    ).read_text()
    assert "no online activation" in document.lower()
    assert "never controls platform features" in document.lower()
