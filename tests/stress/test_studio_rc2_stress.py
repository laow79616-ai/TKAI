"""Bounded concurrent stress checks for local Studio reference components."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import enumerate as active_threads

from studio.backend import SDKStudioGateway, StudioDependencies
from studio.backend.api import StudioAPI
from studio.shared import StudioProject
from tkai.sdk.workflow import Node, WorkflowBuilder, WorkflowRuntime


def test_studio_repositories_and_controllers_remain_consistent_concurrently() -> None:
    """Local project writes and read-only controller calls do not deadlock."""
    before = {thread.ident for thread in active_threads()}
    definition = WorkflowBuilder("stress").add(Node("task", handler="ok")).build()
    dependencies = StudioDependencies.create(
        sdk_gateway=SDKStudioGateway(workflow_runtime=WorkflowRuntime(definition))
    )
    repository = dependencies.project_repository
    api = StudioAPI(dependencies)

    def create(index: int) -> str:
        return repository.create(
            StudioProject(f"project-{index}", "Project")
        ).project_id

    with ThreadPoolExecutor(max_workers=8) as executor:
        identifiers = list(executor.map(create, range(48)))
        reports = list(executor.map(lambda _index: api.health(), range(48)))
    assert len(set(identifiers)) == 48
    assert all(report["status"] == "ok" for report in reports)
    assert {thread.ident for thread in active_threads()} <= before


def test_frontend_reference_store_contracts_have_no_concurrency_side_effects() -> None:
    """Frontend Designer/Monitor/Chat stores remain pure, timer-free declarations."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "studio" / "frontend" / "src"
    sources = (
        (root / "workflow.ts").read_text(encoding="utf-8"),
        (root / "features" / "executions" / "store.ts").read_text(encoding="utf-8"),
        (root / "features" / "chat" / "store.ts").read_text(encoding="utf-8"),
    )
    for source in sources:
        assert "setInterval" not in source
        assert "setTimeout" not in source
        assert "fetch(" not in source
