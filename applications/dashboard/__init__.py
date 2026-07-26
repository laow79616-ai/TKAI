"""Application Center dashboard."""

from typing import Any


def dashboard(center: Any) -> dict[str, Any]:
    return {
        "applications": len(center.catalog.list()),
        "templates": len(center.templates.list()),
        "deployments": len(center.deployments.list()),
        "usage": center.metrics.snapshot(),
        "versions": len(center.versions.list()),
        "permissions": sum(
            len(center.permissions.list(item.id)) for item in center.catalog.list()
        ),
    }
