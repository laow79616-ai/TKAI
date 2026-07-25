"""Dependency-free, deterministic OpenAPI document for the frozen Studio API."""

from __future__ import annotations

from studio.config import StudioSettings

from .contracts import ERROR_SCHEMA, SUCCESS_SCHEMA


def openapi_schema(settings: StudioSettings) -> dict[str, object]:
    """Build the static Studio REST contract without importing or starting FastAPI."""
    prefix = settings.api_prefix.rstrip("/")
    paths: dict[str, object] = {}
    for path, methods in _paths(prefix).items():
        paths[path] = {
            method.lower(): {
                "operationId": operation,
                "responses": {
                    "200": {
                        "description": "Success",
                        "content": {"application/json": {"schema": SUCCESS_SCHEMA}},
                    },
                    "404": {
                        "description": "Not found",
                        "content": {"application/json": {"schema": ERROR_SCHEMA}},
                    },
                    "409": {
                        "description": "Conflict",
                        "content": {"application/json": {"schema": ERROR_SCHEMA}},
                    },
                    "422": {
                        "description": "Validation error",
                        "content": {"application/json": {"schema": ERROR_SCHEMA}},
                    },
                },
            }
            for method, operation in methods
        }
    return {
        "openapi": "3.1.0",
        "info": {"title": settings.app_name, "version": settings.app_version},
        "paths": paths,
        "components": {"schemas": {"Success": SUCCESS_SCHEMA, "Error": ERROR_SCHEMA}},
    }


def _paths(prefix: str) -> dict[str, tuple[tuple[str, str], ...]]:
    """Return the canonical endpoint and operation inventory in stable order."""
    return {
        f"{prefix}/health": (("GET", "health.read"),),
        f"{prefix}/system": (("GET", "system.read"),),
        f"{prefix}/version": (("GET", "version.read"),),
        f"{prefix}/projects": (("GET", "projects.list"), ("POST", "projects.create")),
        f"{prefix}/projects/{{project_id}}": (
            ("GET", "projects.get"),
            ("PATCH", "projects.update"),
            ("DELETE", "projects.delete"),
        ),
        f"{prefix}/workflows": (
            ("GET", "workflows.list"),
            ("POST", "workflows.create"),
        ),
        f"{prefix}/workflows/{{workflow_id}}": (
            ("GET", "workflows.get"),
            ("PATCH", "workflows.update"),
            ("DELETE", "workflows.delete"),
        ),
        f"{prefix}/executions": (
            ("GET", "executions.list"),
            ("POST", "executions.create"),
        ),
        f"{prefix}/executions/{{execution_id}}": (("GET", "executions.get"),),
    }
