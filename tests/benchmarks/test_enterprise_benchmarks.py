"""Offline benchmark validation for Enterprise reference foundations."""

from benchmarks.base import BenchmarkRunner
from benchmarks.report import BenchmarkReport
from enterprise.audit import ReferenceAuditService
from enterprise.license import Edition, LicenseEntitlement, ReferenceLicenseService
from enterprise.tenant import Tenant, TenantRegistry


def test_enterprise_reference_operations_produce_complete_offline_reports() -> None:
    registry = TenantRegistry()
    registry.register(Tenant("tenant-1", "Tenant", "tenant", "org-1"))
    audit = ReferenceAuditService()
    license_service = ReferenceLicenseService(
        (LicenseEntitlement("license-1", Edition.ENTERPRISE),)
    )
    runner = BenchmarkRunner(warmup=1, iterations=5, random_seed=7)
    result = runner.run(
        lambda: (registry.snapshot(), audit.snapshot(), license_service.snapshot())
    )
    assert result.operations == 5 and result.min_latency_ms >= 0
    assert "enterprise" in BenchmarkReport.to_markdown("enterprise", result).lower()
    assert "operations" in BenchmarkReport.to_json("enterprise", result)
