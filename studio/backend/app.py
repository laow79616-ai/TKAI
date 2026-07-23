"""Optional FastAPI adapter for the declarative Studio route inventory."""

from __future__ import annotations

from typing import Any

from studio.config import StudioSettings

from .routes import StudioRouter


def create_fastapi_app(settings: StudioSettings | None = None) -> Any:
    """Create a minimal FastAPI application when the host installs FastAPI.

    FastAPI is intentionally not a dependency of the core TKAI package. A host
    that deploys Studio installs it explicitly, while architecture tests use the
    dependency-free route inventory instead.
    """
    try:
        from fastapi import FastAPI
    except ImportError as error:
        raise RuntimeError(
            "FastAPI is required to create the Studio backend application."
        ) from error

    app = FastAPI(title="TKAI Studio")
    for route in StudioRouter(settings).routes():
        app.add_api_route(
            route.path,
            _placeholder(route.operation_id),
            methods=[route.method],
        )
    return app


def _placeholder(operation_id: str) -> Any:
    """Bind a route's operation identifier without loop-closure ambiguity."""

    async def handler() -> dict[str, str]:
        return {"operation": operation_id}

    return handler
