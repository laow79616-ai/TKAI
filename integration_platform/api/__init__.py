"""FastAPI-compatible Enterprise AI Integration Platform routes."""

from typing import Any

from integration_platform import (
    Connector,
    ConnectorType,
    CredentialReference,
    CredentialType,
    Integration,
    IntegrationPlatform,
    IntegrationScope,
    IntegrationStatus,
)


def register_integration_routes(app: Any, platform: IntegrationPlatform) -> None:
    """Register routes without requiring FastAPI at import time."""

    def add(path: str, endpoint: Any, methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, tags=["integration"])

    def scope(
        tenant: str,
        workspace: str,
        actor: str = "api",
        permissions: str = "integration:read",
    ) -> IntegrationScope:
        return IntegrationScope(
            tenant, workspace, actor, frozenset(permissions.split(","))
        )

    def listed(values: Any) -> dict[str, Any]:
        data = [value.to_dict() for value in values]
        return {"data": data, "total": len(data), "error": None}

    def create_integration(payload: dict[str, Any]) -> dict[str, Any]:
        item = Integration(
            id=str(payload["id"]),
            name=str(payload["name"]),
            description=str(payload["description"]),
            provider=str(payload["provider"]),
            category=str(payload["category"]),
            owner=str(payload["owner"]),
            tenant=str(payload["tenant"]),
            workspace=str(payload["workspace"]),
            status=IntegrationStatus(str(payload.get("status", "draft"))),
            version=str(payload.get("version", "1.0")),
            metadata=dict(payload.get("metadata", {})),
        )
        return platform.create_integration(
            item,
            scope(
                item.tenant,
                item.workspace,
                str(payload.get("actor", "api")),
                str(payload.get("permissions", "integration:write")),
            ),
        ).to_dict()

    def create_credential(payload: dict[str, Any]) -> dict[str, Any]:
        item = CredentialReference(
            str(payload["id"]),
            CredentialType(str(payload["type"])),
            str(payload["reference"]),
            str(payload["tenant"]),
            str(payload["workspace"]),
        )
        return platform.add_credential(
            item,
            scope(
                item.tenant,
                item.workspace,
                str(payload.get("actor", "api")),
                str(payload.get("permissions", "integration:credentials")),
            ),
        ).to_dict()

    def create_connector(payload: dict[str, Any]) -> dict[str, Any]:
        item = Connector(
            id=str(payload["id"]),
            integration_id=str(payload["integration_id"]),
            name=str(payload["name"]),
            type=ConnectorType(str(payload["type"])),
            tenant=str(payload["tenant"]),
            workspace=str(payload["workspace"]),
            credential_reference_id=payload.get("credential_reference_id"),
            base_url=payload.get("base_url"),
        )
        return platform.add_connector(
            item,
            scope(
                item.tenant,
                item.workspace,
                str(payload.get("actor", "api")),
                str(payload.get("permissions", "integration:write")),
            ),
        ).to_dict()

    def collection(name: str) -> Any:
        def endpoint(
            tenant: str,
            workspace: str,
            actor: str = "api",
            permissions: str = "integration:read",
        ) -> dict[str, Any]:
            values = (
                platform.list_integrations(scope(tenant, workspace, actor, permissions))
                if name == "integrations"
                else platform._scoped(
                    getattr(platform, name).values(),
                    scope(tenant, workspace, actor, permissions),
                )
            )
            return listed(values)

        return endpoint

    listing = {
        "/integrations": "integrations",
        "/integration-connectors": "connectors",
        "/integration-credentials": "credentials",
        "/integration-webhooks": "webhooks",
        "/integration-events": "events",
        "/integration-databases": "databases",
        "/integration-storage": "storage",
    }
    for path, name in listing.items():
        add(path, collection(name), ["GET"])
    add(
        "/integration-messaging",
        lambda tenant, workspace: listed(()),
        ["GET"],
    )
    add("/integrations", create_integration, ["POST"])
    add("/integration-connectors", create_connector, ["POST"])
    add("/integration-credentials", create_credential, ["POST"])
    add(
        "/integration-health",
        lambda tenant, workspace, actor="api", permissions="integration:read": {
            "data": platform.health(scope(tenant, workspace, actor, permissions)),
            "error": None,
        },
        ["GET"],
    )
    add(
        "/integration-dashboard",
        lambda tenant, workspace, actor="api", permissions="integration:read": (
            platform.dashboard(scope(tenant, workspace, actor, permissions))
        ),
        ["GET"],
    )
    add("/integration-metrics", platform.metrics.render_prometheus, ["GET"])


__all__ = ("register_integration_routes",)
