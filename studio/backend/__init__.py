"""Studio backend contracts and optional FastAPI application adapter."""

from .app import create_fastapi_app, create_studio_app
from .dependencies import StudioDependencies
from .gateway import SDKStudioGateway, StudioIntegrationError
from .routes import RouteDefinition, StudioRouter
from .services import StudioService

__all__ = (
    "RouteDefinition",
    "SDKStudioGateway",
    "StudioIntegrationError",
    "StudioDependencies",
    "StudioRouter",
    "StudioService",
    "create_fastapi_app",
    "create_studio_app",
)
