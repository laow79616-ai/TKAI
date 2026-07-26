"""Studio API contract namespace shared by backend and future frontend tooling."""

from studio.backend.routes import RouteDefinition, StudioRouter

from .v23 import STUDIO_RESOURCE_PATHS, StudioEndpoint, studio_v23_routes

__all__ = (
    "RouteDefinition",
    "STUDIO_RESOURCE_PATHS",
    "StudioEndpoint",
    "StudioRouter",
    "studio_v23_routes",
)
