"""HTTP adapter for the Enterprise Marketplace."""

from __future__ import annotations

from typing import Any

from marketplace.enterprise_store import EnterpriseMarketplace


class MarketplaceApi:
    """JSON-safe API facade."""

    def __init__(self, marketplace: EnterpriseMarketplace) -> None:
        self.marketplace = marketplace

    def catalog(self) -> dict[str, object]:
        packages = [item.to_dict() for item in self.marketplace.search()]
        return {
            "data": packages,
            "total": len(packages),
            "categories": list(self.marketplace.categories()),
            "tags": list(self.marketplace.tags()),
            "error": None,
        }

    def packages(self) -> dict[str, object]:
        return self.catalog()

    def publishers(self) -> dict[str, object]:
        data = [
            {
                "publisher_id": item.publisher_id,
                "organization": item.organization,
                "display_name": item.display_name,
                "verified": item.verified,
                "owners": list(item.owners),
                "signing_key_id": item.signing_key_id,
            }
            for item in self.marketplace.publishers.values()
        ]
        return {"data": data, "total": len(data), "error": None}

    def licenses(self) -> dict[str, object]:
        data = [
            {
                "license_id": item.license_id,
                "package_id": item.package_id,
                "kind": item.kind.value,
                "seats": item.seats,
                "offline": item.offline,
                "subscription_id": item.subscription_id,
                "active": item.active,
            }
            for item in self.marketplace.licenses.values()
        ]
        return {"data": data, "total": len(data), "error": None}

    def reviews(self) -> dict[str, object]:
        data = [
            {
                "review_id": item.review_id,
                "package_id": item.package_id,
                "author": item.author,
                "rating": item.rating,
                "comment": item.comment,
                "verified_purchase": item.verified_purchase,
                "moderated": item.moderated,
            }
            for item in self.marketplace.reviews.values()
        ]
        return {"data": data, "total": len(data), "error": None}

    def downloads(self) -> dict[str, object]:
        data = [{"package_id": item} for item in self.marketplace.download_log]
        return {"data": data, "total": len(data), "error": None}


def register_marketplace_routes(
    app: Any, marketplace: EnterpriseMarketplace
) -> MarketplaceApi:
    """Register the required read-only enterprise marketplace routes."""
    api = MarketplaceApi(marketplace)
    for path, endpoint in (
        ("/marketplace", api.catalog),
        ("/packages", api.packages),
        ("/publishers", api.publishers),
        ("/licenses", api.licenses),
        ("/reviews", api.reviews),
        ("/downloads", api.downloads),
    ):
        app.add_api_route(path, endpoint, methods=["GET"], tags=["marketplace"])
    return api
