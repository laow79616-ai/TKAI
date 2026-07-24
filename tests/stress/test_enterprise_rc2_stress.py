"""Bounded offline concurrency validation for Enterprise reference components."""

from concurrent.futures import ThreadPoolExecutor

from enterprise.authorization import ReferenceAuthorizationService
from enterprise.license import Edition, LicenseEntitlement, ReferenceLicenseService
from enterprise.tenant import Tenant, TenantRegistry


def test_enterprise_registries_and_services_remain_consistent_under_concurrency() -> (
    None
):
    registry = TenantRegistry()
    licenses = ReferenceLicenseService(
        (LicenseEntitlement("license", Edition.ENTERPRISE),)
    )
    authorization = ReferenceAuthorizationService({})

    def operation(index: int) -> None:
        tenant_id = f"tenant-{index}"
        registry.register(Tenant(tenant_id, tenant_id, tenant_id, "org-1"))
        licenses.get("license")
        authorization.capabilities()

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(operation, range(8)))
    assert len(registry.snapshot()) == 8
