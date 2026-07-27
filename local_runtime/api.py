"""Read-only local-runtime dashboard API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import LocalRuntimeConfig
from .manager import LocalRuntimeManager


def register_local_runtime_routes(app: Any, repository: Path | None = None) -> None:
    """Register dashboard-safe status and health endpoints."""
    root = (repository or Path.cwd()).resolve()

    def manager() -> LocalRuntimeManager:
        return LocalRuntimeManager(LocalRuntimeConfig.load(root))

    app.add_api_route(
        "/local-runtime/status",
        lambda: manager().status(),
        methods=["GET"],
        tags=["local-runtime"],
    )
    app.add_api_route(
        "/local-runtime/health",
        lambda: manager().health(probe_http=False),
        methods=["GET"],
        tags=["local-runtime"],
    )
