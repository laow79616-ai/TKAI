"""GET-only API projections for V7 security metadata."""

from __future__ import annotations

from typing import Any

from ..framework import GLOBAL_SECURITY_FRAMEWORK, SecurityFramework

SECURITY_ENDPOINTS = (
    "policies",
    "roles",
    "permissions",
    "authorization",
    "compliance",
    "secrets",
    "audit",
    "health",
    "metrics",
)


def register_security_framework_routes(
    app: Any, framework: SecurityFramework | None = None
) -> None:
    selected = framework or GLOBAL_SECURITY_FRAMEWORK
    for endpoint in SECURITY_ENDPOINTS:
        app.add_api_route(
            f"/v7/security/{endpoint}",
            lambda endpoint=endpoint: selected.snapshot()[endpoint],
            methods=["GET"],
            tags=["V7 Security Framework"],
        )


__all__ = ("SECURITY_ENDPOINTS", "register_security_framework_routes")
