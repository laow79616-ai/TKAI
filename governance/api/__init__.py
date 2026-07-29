"""FastAPI-compatible Enterprise AI Governance routes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from governance.entities import GovernanceScope
from governance.service import EnterpriseAIGovernancePlatform


def register_governance_routes(
    app: Any, platform: EnterpriseAIGovernancePlatform
) -> None:
    def add(path: str, endpoint: Callable[..., Any], methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, tags=["governance"])

    def scope(tenant: str, workspace: str, actor: str) -> GovernanceScope:
        return GovernanceScope(tenant, workspace, actor)

    def payload_scope(payload: dict[str, Any]) -> GovernanceScope:
        return scope(
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload["actor"]),
        )

    def listed(values: tuple[Any, ...]) -> dict[str, Any]:
        data = [platform.security.redact(value.to_dict()) for value in values]
        return {"data": data, "total": len(data), "error": None}

    def list_endpoint(store: dict[str, Any]) -> Callable[..., dict[str, Any]]:
        def endpoint(tenant: str, workspace: str, actor: str) -> dict[str, Any]:
            return listed(platform.list_records(store, scope(tenant, workspace, actor)))

        return endpoint

    def create_endpoint(
        creator: Callable[[dict[str, Any], GovernanceScope], Any],
    ) -> Callable[[dict[str, Any]], dict[str, Any]]:
        def endpoint(payload: dict[str, Any]) -> dict[str, Any]:
            return creator(payload, payload_scope(payload)).to_dict()

        return endpoint

    def resource_list_endpoint(
        kind: str,
    ) -> Callable[..., dict[str, Any]]:
        def endpoint(tenant: str, workspace: str, actor: str) -> dict[str, Any]:
            values = platform.list_records(
                platform.resources, scope(tenant, workspace, actor)
            )
            return listed(tuple(item for item in values if item.kind == kind))

        return endpoint

    def resource_create_endpoint(
        kind: str,
    ) -> Callable[[dict[str, Any]], dict[str, Any]]:
        def endpoint(payload: dict[str, Any]) -> dict[str, Any]:
            return platform.register_resource(
                kind, payload, payload_scope(payload)
            ).to_dict()

        return endpoint

    stores = {
        "/governance/policies": platform.policies,
        "/governance/risks": platform.risks,
        "/governance/compliance": platform.compliance,
        "/governance/approvals": platform.approvals,
        "/governance/controls": platform.controls,
        "/governance/incidents": platform.incidents,
        "/governance/exceptions": platform.exceptions,
    }
    for path, store in stores.items():
        add(path, list_endpoint(store), ["GET"])

    creators = {
        "/governance/policies": platform.create_policy,
        "/governance/risks": platform.create_risk,
        "/governance/compliance": platform.create_compliance_record,
        "/governance/approvals": platform.request_approval,
        "/governance/controls": platform.create_control,
        "/governance/incidents": platform.create_incident,
        "/governance/exceptions": platform.create_exception,
    }
    for path, creator in creators.items():
        add(path, create_endpoint(creator), ["POST"])

    resource_paths = {
        "/governance/models": "model",
        "/governance/prompts": "prompt",
        "/governance/agents": "agent",
        "/governance/applications": "application",
        "/governance/workflows": "workflow",
    }
    for path, kind in resource_paths.items():
        add(path, resource_list_endpoint(kind), ["GET"])
        add(path, resource_create_endpoint(kind), ["POST"])

    add(
        "/governance/data",
        lambda tenant, workspace, actor: listed(
            tuple(
                item
                for item in platform.list_records(
                    platform.resources, scope(tenant, workspace, actor)
                )
                if item.kind in {"dataset", "knowledge_base"}
            )
        ),
        ["GET"],
    )
    add(
        "/governance/data",
        lambda payload: platform.register_resource(
            str(payload["kind"]),
            dict(payload),
            payload_scope(dict(payload)),
        ).to_dict(),
        ["POST"],
    )
    add(
        "/governance/policies/{policy_id}/status",
        lambda policy_id, payload: platform.transition_policy(
            policy_id,
            str(payload["status"]),
            payload_scope(dict(payload)),
        ).to_dict(),
        ["PATCH"],
    )
    add(
        "/governance/approvals/{approval_id}",
        lambda approval_id, payload: platform.decide_approval(
            approval_id,
            str(payload["decision"]),
            payload_scope(dict(payload)),
        ).to_dict(),
        ["PATCH"],
    )
    add(
        "/governance/evidence",
        lambda payload: platform.record_evidence(
            dict(payload), payload_scope(dict(payload))
        ).to_dict(),
        ["POST"],
    )
    add(
        "/governance/reports",
        lambda tenant, workspace, actor: platform.report(
            scope(tenant, workspace, actor)
        ),
        ["GET"],
    )
    add(
        "/governance/reports/audit-export",
        lambda tenant, workspace, actor, limit=1000: platform.export_audit(
            scope(tenant, workspace, actor), int(limit)
        ),
        ["GET"],
    )
    add(
        "/governance/dashboard",
        lambda tenant, workspace, actor: platform.dashboard(
            scope(tenant, workspace, actor)
        ),
        ["GET"],
    )
