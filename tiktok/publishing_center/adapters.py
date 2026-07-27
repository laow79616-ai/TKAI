"""Bounded integration ports; no implementation bypasses TikTok controls."""

from __future__ import annotations

from typing import Any, Protocol

from .models import PublishingJob


class ReferencePort(Protocol):
    def validate(self, reference: str, tenant: str, workspace: str) -> bool: ...


class PublisherPort(Protocol):
    def publish(self, job: PublishingJob) -> bool: ...


class PolicyPort(Protocol):
    def allowed(self, account: str, tenant: str, workspace: str) -> bool: ...


class AuditPort(Protocol):
    def record(self, event: dict[str, Any]) -> None: ...


class NullReferencePort:
    def validate(self, reference: str, tenant: str, workspace: str) -> bool:
        return bool(reference and tenant and workspace)


class MockPublisherPort:
    """Deterministic local publisher used by tests and development only."""

    def publish(self, job: PublishingJob) -> bool:
        return bool(job.media_reference and job.account_reference)


class AllowPolicyPort:
    def allowed(self, account: str, tenant: str, workspace: str) -> bool:
        return bool(account and tenant and workspace)


class InMemoryAuditPort:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record(self, event: dict[str, Any]) -> None:
        self.events.append(dict(event))


class ExistingContentCenterAdapter:
    def __init__(self, center: Any) -> None:
        self.center = center

    def validate(self, reference: str, tenant: str, workspace: str) -> bool:
        project = getattr(self.center, "projects", {}).get(reference)
        return bool(
            project and project.tenant == tenant and project.workspace == workspace
        )


class ExistingAccountCenterAdapter:
    def __init__(self, center: Any) -> None:
        self.center = center

    def validate(self, reference: str, tenant: str, workspace: str) -> bool:
        account = getattr(self.center, "accounts", {}).get(reference)
        return bool(
            account and account.tenant == tenant and account.workspace == workspace
        )


class ExistingBrowserPublisher:
    def __init__(self, runtime: Any) -> None:
        self.runtime = runtime

    def publish(self, job: PublishingJob) -> bool:
        operation = getattr(self.runtime, "publish_content", None)
        if operation is None:
            return False
        return bool(
            operation(
                job.account_reference,
                {"media_reference": job.media_reference, **job.metadata},
                tenant=job.tenant,
                workspace=job.workspace,
            )
        )


class ExistingProxyPolicy:
    def __init__(self, center: Any) -> None:
        self.center = center

    def allowed(self, account: str, tenant: str, workspace: str) -> bool:
        allocations = getattr(self.center, "allocations", {})
        return not allocations or any(
            item.tenant == tenant
            and item.workspace == workspace
            and item.target_reference == account
            for item in allocations.values()
        )


class ExistingFarmingPolicy:
    def __init__(self, center: Any) -> None:
        self.center = center

    def allowed(self, account: str, tenant: str, workspace: str) -> bool:
        return (
            bool(account)
            and not getattr(self.center, "kill_switch", False)
            and (tenant, workspace)
            not in getattr(self.center, "paused_workspaces", set())
        )
