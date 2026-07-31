"""Read-only V12 dashboard projection catalog."""

from __future__ import annotations

from tkai.v12.api import GET_ROUTES

DASHBOARD_PROJECTIONS = tuple(
    dict.fromkeys(
        path.removeprefix("/v12/").replace("/", " / ").title() for path in GET_ROUTES
    )
)


def dashboard_manifest() -> dict[str, object]:
    return {
        "title": "TKAI V12 Autonomous AI Platform",
        "version": "12.0.0",
        "projection_count": len(DASHBOARD_PROJECTIONS),
        "projections": DASHBOARD_PROJECTIONS,
        "read_only": True,
        "mutation_controls": (),
    }
