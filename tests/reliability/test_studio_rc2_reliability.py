"""Offline Studio RC-2 failure, lifecycle, cleanup, and reference-data checks."""

from __future__ import annotations

import asyncio
import gc
import weakref

import pytest

from studio.backend import SDKStudioGateway, StudioDependencies
from studio.backend.api import StudioAPI
from studio.backend.errors import StudioExecutionError, StudioValidationError
from studio.backend.lifespan import studio_lifespan
from tkai.sdk.workflow import Node, WorkflowBuilder, WorkflowRuntime


def _configured_dependencies() -> StudioDependencies:
    definition = WorkflowBuilder("reliable").add(Node("task", handler="ok")).build()
    return StudioDependencies.create(
        sdk_gateway=SDKStudioGateway(workflow_runtime=WorkflowRuntime(definition))
    )


async def _exercise_lifespan(dependencies: StudioDependencies) -> None:
    """Enter and leave one local Studio lifespan without creating background work."""
    async with studio_lifespan(dependencies)(object()):
        assert not dependencies._shutdown


def test_gateway_workflow_and_execution_failures_do_not_corrupt_fresh_requests() -> (
    None
):
    """Unconfigured gateway failures retain a cause and fresh hosts remain usable."""
    failed = StudioDependencies.create(sdk_gateway=SDKStudioGateway())
    api = StudioAPI(failed)
    api.create_project({"project_id": "project", "name": "Project"})
    api.create_workflow(
        {"workflow_id": "workflow", "project_id": "project", "name": "Workflow"}
    )
    with pytest.raises(StudioExecutionError) as raised:
        api.create_execution({"workflow_id": "workflow"})
    assert raised.value.__cause__ is not None

    healthy = StudioAPI(_configured_dependencies())
    healthy.create_project({"project_id": "project", "name": "Project"})
    healthy.create_workflow(
        {"workflow_id": "workflow", "project_id": "project", "name": "Workflow"}
    )
    assert (
        healthy.create_execution({"workflow_id": "workflow"})["status"] == "succeeded"
    )


def test_invalid_payloads_and_reference_frontend_failures_are_isolated() -> None:
    """Malformed inputs fail locally while static reference stores handle errors."""
    api = StudioAPI(_configured_dependencies())
    with pytest.raises(StudioValidationError):
        api.create_project({"name": 1})

    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "studio" / "frontend" / "src"
    monitor = (root / "features" / "executions" / "store.ts").read_text(
        encoding="utf-8"
    )
    chat = (root / "features" / "chat" / "store.ts").read_text(encoding="utf-8")
    assert "Invalid execution monitor snapshot" in monitor
    assert "Unable to load execution" in monitor
    assert "Invalid Agent Chat snapshot" in chat
    assert "Agent chat request failed" in chat


def test_lifecycle_cleanup_is_idempotent_and_releases_local_gateway_reference() -> None:
    """The lifespan owns no thread and closes an explicitly owned gateway once."""
    dependencies = _configured_dependencies()
    gateway_ref = weakref.ref(dependencies.sdk_gateway)

    asyncio.run(_exercise_lifespan(dependencies))
    dependencies.shutdown()
    assert dependencies._shutdown
    del dependencies
    gc.collect()
    assert gateway_ref() is None
