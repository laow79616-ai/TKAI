"""Transport-neutral API facade for Enterprise Platform resources."""

from typing import Any

from ..platform import EnterprisePlatform


class EnterpriseApi:
    def __init__(self, platform: EnterprisePlatform) -> None:
        self.platform = platform

    def list(self, resource: str, tenant_id: str | None = None) -> dict[str, object]:
        values = self.platform.list_records(resource, tenant_id)
        return {
            "data": [self.platform.serialize(value) for value in values],
            "total": len(values),
        }

    def metrics(self) -> dict[str, int]:
        return self.platform.metrics()


def register_enterprise_platform_routes(
    app: Any, platform: EnterprisePlatform
) -> EnterpriseApi:
    bridge = EnterpriseApi(platform)
    for resource in (
        "organizations",
        "tenants",
        "users",
        "roles",
        "permissions",
        "license",
        "billing",
        "audit",
    ):

        async def endpoint(
            tenant_id: str | None = None, resource: str = resource
        ) -> dict[str, object]:
            return bridge.list(resource, tenant_id)

        app.add_api_route(
            f"/enterprise/{resource}",
            endpoint,
            methods=["GET"],
            tags=["enterprise-platform"],
        )
    app.add_api_route(
        "/enterprise/metrics",
        bridge.metrics,
        methods=["GET"],
        tags=["enterprise-platform"],
    )
    return bridge


__all__ = ("EnterpriseApi", "register_enterprise_platform_routes")
