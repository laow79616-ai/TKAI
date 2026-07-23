"""Studio API contract namespace shared by backend and future frontend tooling."""

from studio.backend.routes import RouteDefinition, StudioRouter

__all__ = ("RouteDefinition", "StudioRouter")
