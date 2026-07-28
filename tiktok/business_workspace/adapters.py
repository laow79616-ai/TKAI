"""Bounded interfaces to existing TikTok services."""

from __future__ import annotations

from typing import Any, Protocol


class CoordinationPort(Protocol):
    def coordinate(
        self,
        target: str,
        reference: str,
        tenant: str,
        workspace: str,
        actor: str,
    ) -> str: ...


class AnalyticsPort(Protocol):
    def workspace_kpis(
        self, workspace_id: str, tenant: str, workspace: str
    ) -> dict[str, float]: ...


class NullCoordinationPort:
    """Offline proposal receiver; it never executes workflows or publishes."""

    def __init__(self) -> None:
        self.proposals: list[dict[str, str]] = []

    def coordinate(
        self,
        target: str,
        reference: str,
        tenant: str,
        workspace: str,
        actor: str,
    ) -> str:
        self.proposals.append(
            {
                "target": target,
                "reference": reference,
                "tenant": tenant,
                "workspace": workspace,
                "actor": actor,
            }
        )
        return f"ref://business-coordination/{target}/{len(self.proposals)}"


class NullAnalyticsPort:
    def workspace_kpis(
        self, workspace_id: str, tenant: str, workspace: str
    ) -> dict[str, float]:
        return {"trend": 0.0, "execution_health": 0.0, "resource_utilization": 0.0}


class ExistingCoordinationAdapter:
    """Calls an existing service's proposal receiver, never an execution method."""

    def __init__(self, service: Any) -> None:
        self.service = service

    def coordinate(
        self,
        target: str,
        reference: str,
        tenant: str,
        workspace: str,
        actor: str,
    ) -> str:
        receiver = getattr(self.service, "accept_business_proposal", None)
        if receiver is None:
            reference_id = reference.rsplit("/", 1)[-1]
            return f"ref://business-coordination/{target}/{reference_id}"
        return str(receiver(reference, tenant, workspace, actor))


class ExistingAnalyticsAdapter:
    def __init__(self, service: Any) -> None:
        self.service = service

    def workspace_kpis(
        self, workspace_id: str, tenant: str, workspace: str
    ) -> dict[str, float]:
        reader = getattr(self.service, "workspace_kpis", None)
        if reader is None:
            return NullAnalyticsPort().workspace_kpis(workspace_id, tenant, workspace)
        return dict(reader(workspace_id, tenant, workspace))
