"""Declarative REST route inventory independent from the optional FastAPI adapter."""

from __future__ import annotations

from dataclasses import dataclass

from studio.config import StudioSettings


@dataclass(frozen=True, slots=True)
class RouteDefinition:
    """A stable REST endpoint descriptor consumed by the backend adapter."""

    method: str
    path: str
    operation_id: str


class StudioRouter:
    """Expose the initial Studio REST route contract in deterministic order."""

    def __init__(self, settings: StudioSettings | None = None) -> None:
        self._settings = settings or StudioSettings()

    def routes(self) -> tuple[RouteDefinition, ...]:
        """Return project, workflow, execution, health, and system endpoints."""
        prefix = self._settings.api_prefix.rstrip("/")
        return (
            RouteDefinition("GET", f"{prefix}/health", "health.read"),
            RouteDefinition("GET", f"{prefix}/system", "system.read"),
            RouteDefinition("GET", f"{prefix}/projects", "projects.list"),
            RouteDefinition("POST", f"{prefix}/projects", "projects.create"),
            RouteDefinition(
                "GET", f"{prefix}/workflows/{{workflow_id}}", "workflows.get"
            ),
            RouteDefinition("POST", f"{prefix}/workflows", "workflows.save"),
            RouteDefinition("POST", f"{prefix}/executions", "executions.create"),
        )
