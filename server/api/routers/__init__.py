"""Read-only route adapters for the optional HTTP host."""

from .health import endpoint as health_endpoint
from .metadata import endpoint as metadata_endpoint
from .package import get_endpoint as get_package_endpoint
from .package import list_endpoint as list_package_endpoint
from .publisher import get_endpoint as get_publisher_endpoint
from .publisher import list_endpoint as list_publisher_endpoint
from .registry import get_endpoint as get_registry_endpoint
from .registry import list_endpoint as list_registry_endpoint
from .search import endpoint as search_endpoint
from .statistics import endpoint as statistics_endpoint
from .version import endpoint as version_endpoint
from .version import get_endpoint as get_version_endpoint
from .version import list_endpoint as list_version_endpoint

__all__ = (
    "get_package_endpoint",
    "get_publisher_endpoint",
    "get_registry_endpoint",
    "get_version_endpoint",
    "health_endpoint",
    "list_package_endpoint",
    "list_publisher_endpoint",
    "list_registry_endpoint",
    "list_version_endpoint",
    "metadata_endpoint",
    "search_endpoint",
    "statistics_endpoint",
    "version_endpoint",
)
