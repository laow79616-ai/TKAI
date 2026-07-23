"""Lifecycle and error-mapping tests for explicit Studio dependencies."""

from __future__ import annotations

import asyncio

from studio.backend import StudioDependencies
from studio.backend.errors import StudioNotFoundError
from studio.backend.lifespan import studio_lifespan
from studio.backend.middleware import error_payload, error_status, request_id


def test_lifespan_and_shutdown_are_idempotent() -> None:
    """No background task is created and repeated local shutdown is safe."""
    dependencies = StudioDependencies.create()

    async def exercise() -> None:
        async with studio_lifespan(dependencies)(object()):
            assert not dependencies._shutdown

    asyncio.run(exercise())
    dependencies.shutdown()
    assert dependencies._shutdown


def test_error_mapping_and_request_ids_are_stable() -> None:
    """API helpers do not expose tracebacks or mutate caller-provided request ids."""
    error = StudioNotFoundError("Project not found: p1")
    identifier = request_id("client-1")

    assert identifier == "client-1"
    assert error_status(error) == 404
    assert error_payload(error, identifier) == {
        "error": "StudioNotFoundError",
        "message": "Project not found: p1",
        "request_id": "client-1",
    }
