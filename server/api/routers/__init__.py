"""Read-only route adapters for the optional HTTP host."""

from .health import endpoint as health_endpoint
from .metadata import endpoint as metadata_endpoint
from .version import endpoint as version_endpoint

__all__ = ("health_endpoint", "metadata_endpoint", "version_endpoint")
