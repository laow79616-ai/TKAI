"""Tests for the dependency-free Studio REST route inventory."""

from __future__ import annotations

from studio.backend.routes import StudioRouter
from studio.config import StudioSettings


def test_router_exposes_initial_rest_contract_in_stable_order() -> None:
    """Project, workflow, execution, health, and system routes are declarative."""
    routes = StudioRouter(StudioSettings(api_prefix="/studio")).routes()

    assert [(route.method, route.operation_id) for route in routes] == [
        ("GET", "health.read"),
        ("GET", "system.read"),
        ("GET", "projects.list"),
        ("POST", "projects.create"),
        ("GET", "workflows.get"),
        ("POST", "workflows.save"),
        ("POST", "executions.create"),
    ]
    assert all(route.path.startswith("/studio/") for route in routes)
