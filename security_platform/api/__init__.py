"""FastAPI-compatible Enterprise AI Security Platform routes."""

from typing import Any

from security_platform import (
    AuthenticationRequest,
    Identity,
    IdentityKind,
    IncidentSeverity,
    SecretReference,
    SecurityPlatform,
    SecurityScope,
)


def register_security_routes(app: Any, platform: SecurityPlatform) -> None:
    def add(path: str, endpoint: Any, methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, tags=["security"])

    def scope(tenant: str, workspace: str, actor: str = "dashboard") -> SecurityScope:
        return SecurityScope(tenant, workspace, actor)

    def listed(values: Any) -> dict[str, Any]:
        data = [value.to_dict() for value in values]
        return {"data": data, "total": len(data), "error": None}

    add(
        "/security/identity",
        lambda tenant, workspace, actor="dashboard": listed(
            platform.list_identities(scope(tenant, workspace, actor))
        ),
        ["GET"],
    )
    add(
        "/security/identity",
        lambda payload: platform.create_identity(
            Identity(
                str(payload["id"]),
                IdentityKind(str(payload["kind"])),
                str(payload["tenant"]),
                str(payload["workspace"]),
                str(payload["display_name"]),
                bool(payload.get("enabled", True)),
                dict(payload.get("attributes", {})),
            ),
            scope(
                str(payload["tenant"]),
                str(payload["workspace"]),
                str(payload.get("actor", "dashboard")),
            ),
        ).to_dict(),
        ["POST"],
    )
    add(
        "/security/auth",
        lambda payload: platform.authenticate(
            AuthenticationRequest(
                str(payload["method"]),
                str(payload["identity_id"]),
                str(payload["credential"]),
                str(payload["tenant"]),
                str(payload["workspace"]),
                str(payload["mfa_code"]) if payload.get("mfa_code") else None,
            )
        ).to_dict(),
        ["POST"],
    )
    add(
        "/security/policy",
        lambda identity_id, action, resource, tenant, workspace, actor="dashboard": (
            platform.authorize(
                identity_id,
                action,
                resource,
                scope(tenant, workspace, actor),
            ).to_dict()
        ),
        ["GET"],
    )
    add(
        "/security/secrets",
        lambda: listed(platform.secret_references.values()),
        ["GET"],
    )
    add(
        "/security/secrets",
        lambda payload: platform.add_secret_reference(
            SecretReference(
                str(payload["name"]),
                str(payload["provider"]),
                str(payload["path"]),
                str(payload["version"]) if payload.get("version") else None,
            ),
            scope(
                str(payload["tenant"]),
                str(payload["workspace"]),
                str(payload.get("actor", "dashboard")),
            ),
        ).to_dict(),
        ["POST"],
    )
    add(
        "/security/incidents",
        lambda tenant, workspace: listed(
            item
            for item in platform.incidents.values()
            if item.tenant == tenant and item.workspace == workspace
        ),
        ["GET"],
    )
    add(
        "/security/incidents",
        lambda payload: platform.create_incident(
            str(payload["id"]),
            str(payload["title"]),
            IncidentSeverity(str(payload["severity"])),
            scope(
                str(payload["tenant"]),
                str(payload["workspace"]),
                str(payload.get("actor", "dashboard")),
            ),
            str(payload["owner"]) if payload.get("owner") else None,
        ).to_dict(),
        ["POST"],
    )
    add(
        "/security/compliance",
        lambda: {
            "mappings": len(platform.compliance_mappings),
            "evidence": len(platform.evidence),
            "exceptions": len(platform.exceptions),
        },
        ["GET"],
    )
    add(
        "/security/dashboard",
        lambda tenant, workspace, actor="dashboard": platform.dashboard(
            scope(tenant, workspace, actor)
        ),
        ["GET"],
    )


__all__ = ("register_security_routes",)
