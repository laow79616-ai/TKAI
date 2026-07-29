"""Bounded interfaces to completed TikTok modules."""

from __future__ import annotations

from typing import Any, Protocol


class ReferencePort(Protocol):
    def exists(self, reference: str, tenant: str, workspace: str) -> bool: ...


class StatusPort(Protocol):
    def status(self, reference: str, tenant: str, workspace: str) -> str: ...


class AnalyticsPort(Protocol):
    def campaign_kpis(
        self, campaign_id: str, tenant: str, workspace: str
    ) -> dict[str, float]: ...


class PlanningPort(Protocol):
    def register_campaign_plan(
        self, campaign_id: str, references: dict[str, Any], tenant: str, workspace: str
    ) -> str: ...


class NullReferencePort:
    def exists(self, reference: str, tenant: str, workspace: str) -> bool:
        return bool(reference and tenant and workspace)


class NullStatusPort:
    def status(self, reference: str, tenant: str, workspace: str) -> str:
        return "not_configured" if not reference else "available"


class NullAnalyticsPort:
    def campaign_kpis(
        self, campaign_id: str, tenant: str, workspace: str
    ) -> dict[str, float]:
        return {
            "publishing_performance": 0.0,
            "execution_performance": 0.0,
            "resource_usage": 0.0,
            "completion_rate": 0.0,
            "trend": 0.0,
        }


class NullPlanningPort:
    """Offline adapter that coordinates a plan but never executes or publishes."""

    def __init__(self) -> None:
        self.registered: list[dict[str, Any]] = []

    def register_campaign_plan(
        self, campaign_id: str, references: dict[str, Any], tenant: str, workspace: str
    ) -> str:
        self.registered.append(
            {
                "campaign_id": campaign_id,
                "references": references,
                "tenant": tenant,
                "workspace": workspace,
            }
        )
        return f"ref://operations-plan/{campaign_id}"


class ExistingRegistryAdapter:
    """Read-only adapter for an existing module's scoped registry."""

    def __init__(self, service: Any, collection: str) -> None:
        self.service = service
        self.collection = collection

    def exists(self, reference: str, tenant: str, workspace: str) -> bool:
        reference_id = reference.rsplit("/", 1)[-1]
        item = getattr(self.service, self.collection, {}).get(reference_id)
        return bool(item and item.tenant == tenant and item.workspace == workspace)


class ExistingStatusAdapter:
    def __init__(self, service: Any, collection: str) -> None:
        self.service = service
        self.collection = collection

    def status(self, reference: str, tenant: str, workspace: str) -> str:
        if not reference:
            return "not_configured"
        reference_id = reference.rsplit("/", 1)[-1]
        item = getattr(self.service, self.collection, {}).get(reference_id)
        if not item or item.tenant != tenant or item.workspace != workspace:
            return "unavailable"
        status = getattr(item, "status", "available")
        return str(getattr(status, "value", status))


class ExistingAnalyticsAdapter:
    def __init__(self, service: Any) -> None:
        self.service = service

    def campaign_kpis(
        self, campaign_id: str, tenant: str, workspace: str
    ) -> dict[str, float]:
        reader = getattr(self.service, "campaign_kpis", None)
        if reader is None:
            return NullAnalyticsPort().campaign_kpis(campaign_id, tenant, workspace)
        return dict(reader(campaign_id, tenant, workspace))


class ExistingPlannerAdapter:
    def __init__(self, service: Any) -> None:
        self.service = service

    def register_campaign_plan(
        self, campaign_id: str, references: dict[str, Any], tenant: str, workspace: str
    ) -> str:
        receiver = getattr(self.service, "accept_campaign_plan", None)
        if receiver is None:
            return f"ref://operations-plan/{campaign_id}"
        return str(receiver(campaign_id, references, tenant, workspace))
