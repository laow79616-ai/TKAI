"""Sprint-8 Enterprise AI Studio API inventory."""

from __future__ import annotations

from dataclasses import dataclass

STUDIO_RESOURCE_PATHS = (
    "/projects",
    "/prompts",
    "/chat",
    "/sessions",
    "/knowledge",
    "/rag",
    "/models",
    "/evaluation",
    "/workflows",
)


@dataclass(frozen=True, slots=True)
class StudioEndpoint:
    method: str
    path: str
    operation_id: str


def studio_v23_routes(prefix: str = "/api") -> tuple[StudioEndpoint, ...]:
    """Return the stable V2.3 resource collection API."""
    base = prefix.rstrip("/")
    return tuple(
        endpoint
        for resource in STUDIO_RESOURCE_PATHS
        for endpoint in (
            StudioEndpoint("GET", f"{base}{resource}", f"{resource[1:]}.list"),
            StudioEndpoint("POST", f"{base}{resource}", f"{resource[1:]}.create"),
        )
    )


__all__ = ("STUDIO_RESOURCE_PATHS", "StudioEndpoint", "studio_v23_routes")
