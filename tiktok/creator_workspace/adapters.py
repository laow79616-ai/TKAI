"""Bounded ports for coordinating existing TikTok services."""

from __future__ import annotations

from typing import Any, Protocol

from .models import PublishingPlanRequest


class ContentCenterPort(Protocol):
    def project_exists(self, reference: str, tenant: str, workspace: str) -> bool: ...


class PublishingCenterPort(Protocol):
    def submit_plan(self, request: PublishingPlanRequest) -> str: ...


class AnalyticsCenterPort(Protocol):
    def workspace_statistics(self, tenant: str, workspace: str) -> dict[str, Any]: ...


class CoordinationPort(Protocol):
    def reference_exists(self, reference: str, tenant: str, workspace: str) -> bool: ...


class NullContentCenter:
    def project_exists(self, reference: str, tenant: str, workspace: str) -> bool:
        return bool(reference and tenant and workspace)


class NullPublishingCenter:
    """Offline test double; it records a plan and never publishes."""

    def __init__(self) -> None:
        self.submitted: list[PublishingPlanRequest] = []

    def submit_plan(self, request: PublishingPlanRequest) -> str:
        self.submitted.append(request)
        return f"publishing-plan://{request.publishing_plan_reference}"


class NullAnalyticsCenter:
    def workspace_statistics(self, tenant: str, workspace: str) -> dict[str, Any]:
        return {"tenant": tenant, "workspace": workspace, "publishing": {}}


class NullCoordinationPort:
    def reference_exists(self, reference: str, tenant: str, workspace: str) -> bool:
        return bool(reference and tenant and workspace)


class ExistingContentCenterAdapter:
    def __init__(self, center: Any) -> None:
        self.center = center

    def project_exists(self, reference: str, tenant: str, workspace: str) -> bool:
        project = getattr(self.center, "projects", {}).get(reference)
        return bool(
            project and project.tenant == tenant and project.workspace == workspace
        )


class ExistingPublishingCenterAdapter:
    """Submits to an existing publishing planning boundary, never its executor."""

    def __init__(self, center: Any) -> None:
        self.center = center

    def submit_plan(self, request: PublishingPlanRequest) -> str:
        queue_plan = getattr(self.center, "accept_creator_plan", None)
        if queue_plan is not None:
            return str(queue_plan(request))
        return f"publishing-plan://{request.publishing_plan_reference}"


class ExistingAnalyticsCenterAdapter:
    def __init__(self, center: Any) -> None:
        self.center = center

    def workspace_statistics(self, tenant: str, workspace: str) -> dict[str, Any]:
        exporter = getattr(self.center, "workspace_statistics", None)
        if exporter is None:
            return {}
        return dict(exporter(tenant=tenant, workspace=workspace))


class ExistingRegistryAdapter:
    def __init__(self, service: Any, collection: str) -> None:
        self.service = service
        self.collection = collection

    def reference_exists(self, reference: str, tenant: str, workspace: str) -> bool:
        item = getattr(self.service, self.collection, {}).get(reference)
        return bool(item and item.tenant == tenant and item.workspace == workspace)
