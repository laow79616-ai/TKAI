"""Optional FastAPI application factory for read-only Marketplace Server routes."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from os import environ
from types import ModuleType
from typing import Any, cast

from server.production import ProductionConfigurationLoader, ProductionRuntime

from .auth.router import register_routes as register_auth_routes
from .dependencies import ApiDependencies
from .errors import (
    authentication_error_type,
    foundation_error_types,
    foundation_exception_handler,
)
from .middleware import (
    ExceptionMiddleware,
    ObservabilityMiddleware,
    RateLimitMiddleware,
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
)
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
    production_runtime: ProductionRuntime | None = None,
) -> Any:
    """Create an isolated FastAPI application with only read-only endpoints.

    FastAPI remains an optional host dependency. Tests and embedding callers can
    inject a compatible factory; this module never starts a server or performs
    network I/O.
    """
    selected = dependencies or ApiDependencies.create()
    runtime = production_runtime or ProductionRuntime(
        ProductionConfigurationLoader.load(environment=environ),
        closers=_dependency_closers(selected),
    )
    fastapi_module = _fastapi_module() if app_factory is None else None
    factory = (
        cast(Callable[..., Any], fastapi_module.FastAPI)
        if fastapi_module is not None
        else app_factory
    )
    if factory is None:
        raise RuntimeError("An HTTP application factory is required.")
    app = factory(
        **openapi_metadata(selected.server_config),
        docs_url="/docs",
        openapi_url="/openapi.json",
    )
    _attach_dependencies(app, selected)
    _attach_production_runtime(app, runtime)
    app.add_middleware(ExceptionMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware, runtime=runtime)
    app.add_middleware(RateLimitMiddleware, runtime=runtime)
    app.add_middleware(ObservabilityMiddleware, runtime=runtime)
    for error_type in (*foundation_error_types(), authentication_error_type()):
        app.add_exception_handler(error_type, foundation_exception_handler)
    register_auth_routes(
        app,
        selected.authentication_service,
        fastapi_module=fastapi_module,
    )
    app.add_api_route(
        "/health", health_endpoint(selected), methods=["GET"], tags=["health"]
    )
    app.add_api_route(
        "/health/live",
        lambda: runtime.health.snapshot().to_dict(),
        methods=["GET"],
        tags=["health"],
    )
    app.add_api_route(
        "/health/ready",
        lambda: runtime.health.snapshot().to_dict(),
        methods=["GET"],
        tags=["health"],
    )
    app.add_api_route(
        "/health/startup",
        lambda: runtime.health.snapshot().to_dict(),
        methods=["GET"],
        tags=["health"],
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


def _fastapi_module() -> ModuleType:
    """Load FastAPI only when a real HTTP application is explicitly requested."""
    try:
        return cast(ModuleType, import_module("fastapi"))
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "FastAPI is required to create the Marketplace Server HTTP application."
        ) from error


def _attach_dependencies(app: Any, dependencies: ApiDependencies) -> None:
    """Attach dependencies to this app only; no process-wide singleton is used."""
    if not hasattr(app, "state"):
        app.state = type("ApiState", (), {})()
    app.state.api_dependencies = dependencies


def _attach_production_runtime(app: Any, runtime: ProductionRuntime) -> None:
    """Attach and lifecycle-manage runtime state on this app instance only."""
    if not hasattr(app, "state"):
        app.state = type("ApiState", (), {})()
    app.state.production_runtime = runtime
    if hasattr(app, "add_event_handler"):
        app.add_event_handler("startup", runtime.start)
        app.add_event_handler("shutdown", runtime.close)


def _dependency_closers(
    dependencies: ApiDependencies,
) -> tuple[Callable[[], None], ...]:
    """Collect explicit service close methods without modifying Foundation contracts."""
    services = (
        dependencies.health_service,
        dependencies.authentication_service,
        dependencies.registry_service,
        dependencies.publisher_service,
        dependencies.package_service,
        dependencies.version_service,
        dependencies.search_service,
        dependencies.statistics_service,
    )
    closers: list[Callable[[], None]] = []
    for service in services:
        close = getattr(service, "close", None)
        if callable(close):
            closers.append(cast(Callable[[], None], close))
    return tuple(closers)
