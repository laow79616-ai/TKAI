"""Optional FastAPI application factory for read-only Marketplace Server routes."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any, cast

from .dependencies import ApiDependencies
from .errors import foundation_error_types, foundation_exception_handler
from .middleware import ExceptionMiddleware, RequestIdMiddleware
from .models import ApiListResponse, ApiResourceResponse
from .openapi import openapi_metadata
from .routers import (
    get_package_endpoint,
    get_publisher_endpoint,
    get_registry_endpoint,
    get_version_endpoint,
    health_endpoint,
    list_package_endpoint,
    list_publisher_endpoint,
    list_registry_endpoint,
    list_version_endpoint,
    metadata_endpoint,
    search_endpoint,
    statistics_endpoint,
    version_endpoint,
)


def create_app(
    *,
    dependencies: ApiDependencies | None = None,
    app_factory: Callable[..., Any] | None = None,
) -> Any:
    """Create an isolated FastAPI application with only read-only endpoints.

    FastAPI remains an optional host dependency. Tests and embedding callers can
    inject a compatible factory; this module never starts a server or performs
    network I/O.
    """
    selected = dependencies or ApiDependencies.create()
    factory = app_factory or _fastapi_factory()
    app = factory(
        **openapi_metadata(selected.server_config),
        docs_url="/docs",
        openapi_url="/openapi.json",
    )
    _attach_dependencies(app, selected)
    app.add_middleware(ExceptionMiddleware)
    app.add_middleware(RequestIdMiddleware)
    for error_type in foundation_error_types():
        app.add_exception_handler(error_type, foundation_exception_handler)
    app.add_api_route(
        "/health", health_endpoint(selected), methods=["GET"], tags=["health"]
    )
    app.add_api_route(
        "/version", version_endpoint(selected), methods=["GET"], tags=["server"]
    )
    app.add_api_route(
        "/metadata", metadata_endpoint(selected), methods=["GET"], tags=["server"]
    )
    app.add_api_route(
        "/registry",
        list_registry_endpoint(selected),
        methods=["GET"],
        tags=["registry"],
        response_model=ApiListResponse,
    )
    app.add_api_route(
        "/registry/{registry_id}",
        get_registry_endpoint(selected),
        methods=["GET"],
        tags=["registry"],
        response_model=ApiResourceResponse,
    )
    app.add_api_route(
        "/publishers",
        list_publisher_endpoint(selected),
        methods=["GET"],
        tags=["publisher"],
        response_model=ApiListResponse,
    )
    app.add_api_route(
        "/publishers/{publisher_id}",
        get_publisher_endpoint(selected),
        methods=["GET"],
        tags=["publisher"],
        response_model=ApiResourceResponse,
    )
    app.add_api_route(
        "/packages",
        list_package_endpoint(selected),
        methods=["GET"],
        tags=["package"],
        response_model=ApiListResponse,
    )
    app.add_api_route(
        "/packages/{package_id}",
        get_package_endpoint(selected),
        methods=["GET"],
        tags=["package"],
        response_model=ApiResourceResponse,
    )
    app.add_api_route(
        "/versions",
        list_version_endpoint(selected),
        methods=["GET"],
        tags=["version"],
        response_model=ApiListResponse,
    )
    app.add_api_route(
        "/versions/{version_id}",
        get_version_endpoint(selected),
        methods=["GET"],
        tags=["version"],
        response_model=ApiResourceResponse,
    )
    app.add_api_route(
        "/search", search_endpoint(selected), methods=["GET"], tags=["search"]
    )
    app.add_api_route(
        "/statistics",
        statistics_endpoint(selected),
        methods=["GET"],
        tags=["statistics"],
    )
    return app


def _fastapi_factory() -> Callable[..., Any]:
    """Load FastAPI only when a real HTTP application is explicitly requested."""
    try:
        module = import_module("fastapi")
        return cast(Callable[..., Any], module.FastAPI)
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "FastAPI is required to create the Marketplace Server HTTP application."
        ) from error


def _attach_dependencies(app: Any, dependencies: ApiDependencies) -> None:
    """Attach dependencies to this app only; no process-wide singleton is used."""
    if not hasattr(app, "state"):
        app.state = type("ApiState", (), {})()
    app.state.api_dependencies = dependencies
