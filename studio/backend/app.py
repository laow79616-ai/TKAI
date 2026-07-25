"""Optional FastAPI Studio application host with explicit dependency wiring."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any, cast

from studio.config import StudioSettings

from .api import StudioAPI
from .dependencies import StudioDependencies
from .lifespan import studio_lifespan


def create_studio_app(
    *,
    dependencies: StudioDependencies | None = None,
    settings: StudioSettings | None = None,
    app_factory: Callable[..., Any] | None = None,
) -> Any:
    """Create a FastAPI host without constructing a provider or V1.x runtime.

    ``app_factory`` is an explicit test seam. Production callers omit it and
    must install FastAPI as a Studio-host dependency.
    """
    selected = dependencies or StudioDependencies.create(settings=settings)
    factory = app_factory or _fastapi_factory()
    active_settings = selected.settings
    app = factory(
        title=active_settings.app_name,
        version=active_settings.app_version,
        description="TKAI Studio backend API",
        docs_url="/docs" if active_settings.docs_enabled else None,
        openapi_url="/openapi.json" if active_settings.docs_enabled else None,
        lifespan=studio_lifespan(selected),
    )
    _attach_state(app, selected)
    _register_routes(app, StudioAPI(selected), active_settings.api_prefix)
    return app


def create_fastapi_app(settings: StudioSettings | None = None) -> Any:
    """Compatibility alias for the Sprint-1 optional FastAPI app factory."""
    return create_studio_app(settings=settings)


def _fastapi_factory() -> Callable[..., Any]:
    """Load FastAPI only when a caller explicitly creates the application host."""
    try:
        module = import_module("fastapi")
        return cast(Callable[..., Any], module.FastAPI)
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "FastAPI is required to create the Studio backend application."
        ) from error


def _attach_state(app: Any, dependencies: StudioDependencies) -> None:
    """Attach explicitly composed dependencies to app state after construction."""
    if not hasattr(app, "state"):
        app.state = type("StudioState", (), {})()
    app.state.studio_dependencies = dependencies


def _register_routes(app: Any, api: StudioAPI, prefix: str) -> None:
    """Attach REST handlers; registration itself does not perform SDK execution."""
    base = prefix.rstrip("/")
    app.add_api_route(f"{base}/health", api.health, methods=["GET"])
    app.add_api_route(f"{base}/system", api.system, methods=["GET"])
    app.add_api_route(f"{base}/version", api.version, methods=["GET"])
    app.add_api_route(f"{base}/projects", api.create_project, methods=["POST"])
    app.add_api_route(f"{base}/projects", api.list_projects, methods=["GET"])
    app.add_api_route(
        f"{base}/projects/{{project_id}}", api.get_project, methods=["GET"]
    )
    app.add_api_route(
        f"{base}/projects/{{project_id}}", api.update_project, methods=["PATCH"]
    )
    app.add_api_route(
        f"{base}/projects/{{project_id}}", api.delete_project, methods=["DELETE"]
    )
    app.add_api_route(f"{base}/workflows", api.create_workflow, methods=["POST"])
    app.add_api_route(f"{base}/workflows", api.list_workflows, methods=["GET"])
    app.add_api_route(
        f"{base}/workflows/{{workflow_id}}", api.get_workflow, methods=["GET"]
    )
    app.add_api_route(
        f"{base}/workflows/{{workflow_id}}", api.update_workflow, methods=["PATCH"]
    )
    app.add_api_route(
        f"{base}/workflows/{{workflow_id}}", api.delete_workflow, methods=["DELETE"]
    )
    app.add_api_route(f"{base}/executions", api.create_execution, methods=["POST"])
    app.add_api_route(f"{base}/executions", api.list_executions, methods=["GET"])
    app.add_api_route(
        f"{base}/executions/{{execution_id}}", api.get_execution, methods=["GET"]
    )
