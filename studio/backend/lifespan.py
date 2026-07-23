"""FastAPI-compatible lifecycle manager for explicitly composed Studio dependencies."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from .dependencies import StudioDependencies


def studio_lifespan(dependencies: StudioDependencies) -> Any:
    """Return an async lifecycle manager with idempotent dependency shutdown."""

    @asynccontextmanager
    async def lifespan(_: object) -> AsyncIterator[None]:
        try:
            yield
        finally:
            dependencies.shutdown()

    return lifespan
