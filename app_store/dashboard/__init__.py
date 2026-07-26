"""Enterprise App Store dashboard projection."""

from app_store.models import Scope
from app_store.service import EnterpriseAppStore

SECTIONS = (
    "Store Home",
    "Categories",
    "Application Details",
    "Installed Applications",
    "Updates",
    "Licenses",
    "Subscriptions",
    "Publishers",
    "Reviews",
    "Moderation",
    "Analytics",
)


def dashboard(store: EnterpriseAppStore, scope: Scope) -> dict[str, object]:
    installations = tuple(
        item for item in store.installations.values() if item.scope == scope
    )
    return {
        "sections": SECTIONS,
        "applications": [item.to_dict() for item in store.catalog(scope)],
        "installed": [item.to_dict() for item in installations],
        "updates": {
            item.id: [package.to_dict() for package in store.available_updates(item.id)]
            for item in installations
        },
        "analytics": store.analytics(scope),
        "metrics": store.metrics.snapshot(),
    }
