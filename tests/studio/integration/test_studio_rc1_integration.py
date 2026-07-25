"""Offline, bounded integration checks across Studio's frozen product layers."""

from __future__ import annotations

import runpy
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from studio.backend import SDKStudioGateway, StudioDependencies
from studio.backend.api import StudioAPI, openapi_schema
from studio.backend.api.contracts import error, success
from studio.backend.errors import StudioExecutionError, StudioValidationError
from studio.shared import StudioProject
from tkai.sdk.workflow import Node, WorkflowBuilder, WorkflowRuntime


def _dependencies() -> StudioDependencies:
    definition = WorkflowBuilder("reference").add(Node("task", handler="done")).build()
    return StudioDependencies.create(
        sdk_gateway=SDKStudioGateway(workflow_runtime=WorkflowRuntime(definition))
    )


def test_full_project_workflow_execution_chain_and_frozen_health_contract() -> None:
    """Reference services compose through the public SDK WorkflowRuntime only."""
    dependencies = _dependencies()
    api = StudioAPI(dependencies)
    project = api.create_project({"project_id": "project", "name": "Project"})
    workflow = api.create_workflow(
        {
            "workflow_id": "workflow",
            "project_id": project["project_id"],
            "name": "Workflow",
            "nodes": [],
            "edges": [],
        }
    )
    assert api.get_project("project")["name"] == "Project"
    updated = api.update_project("project", {"description": "updated"})
    assert updated["description"] == "updated"
    assert api.list_workflows("project") == [workflow]
    assert api.update_workflow("workflow", workflow)["workflow_id"] == "workflow"
    execution = api.create_execution({"workflow_id": "workflow"})
    assert execution["status"] == "succeeded"
    assert api.get_execution(execution["execution_id"])["output"] == "done"
    assert api.list_executions(workflow_id="workflow") == [execution]
    assert api.health()["status"] == "ok"
    assert "studio" in api.system() and "tkai_version" in api.version()
    assert api.delete_workflow("workflow") == {"deleted": "workflow"}
    assert api.delete_project("project") == {"deleted": "project"}


def test_frozen_openapi_and_response_envelopes_remain_stable() -> None:
    """The integration baseline locks routes and JSON envelope shapes, offline."""
    schema = openapi_schema(StudioDependencies.create().settings)
    for path in ("/api/projects", "/api/workflows", "/api/executions", "/api/version"):
        assert path in schema["paths"]
    assert set(schema["components"]["schemas"]) == {"Success", "Error"}
    assert set(success({"value": 1}, "request-1")) == {
        "success",
        "data",
        "request_id",
        "timestamp",
    }
    assert set(error("Invalid", "safe", "request-1")) == {
        "success",
        "error",
        "request_id",
        "timestamp",
    }


def test_invalid_workflow_and_gateway_failure_are_isolated() -> None:
    """A failed request preserves exception chaining and does not poison a new host."""
    invalid_api = StudioAPI(StudioDependencies.create())
    with pytest.raises(StudioValidationError):
        invalid_api.create_workflow({})

    failed = StudioDependencies.create(sdk_gateway=SDKStudioGateway())
    failed_api = StudioAPI(failed)
    failed_api.create_project({"project_id": "project", "name": "Project"})
    failed_api.create_workflow(
        {"workflow_id": "workflow", "project_id": "project", "name": "Workflow"}
    )
    with pytest.raises(StudioExecutionError) as raised:
        failed_api.create_execution({"workflow_id": "workflow"})
    assert raised.value.__cause__ is not None

    healthy_api = StudioAPI(_dependencies())
    healthy_api.create_project({"project_id": "project", "name": "Project"})
    healthy_api.create_workflow(
        {"workflow_id": "workflow", "project_id": "project", "name": "Workflow"}
    )
    execution = healthy_api.create_execution({"workflow_id": "workflow"})
    assert execution["status"] == "succeeded"


def test_repositories_are_thread_safe_for_bounded_concurrent_creates() -> None:
    """Concurrent local reference writes neither lose entries nor duplicate ids."""
    repository = StudioDependencies.create().project_repository

    def create(index: int) -> str:
        project = repository.create(StudioProject(f"project-{index}", "Project"))
        return project.project_id

    with ThreadPoolExecutor(max_workers=8) as executor:
        identifiers = list(executor.map(create, range(32)))
    assert set(identifiers) == {f"project-{index}" for index in range(32)}
    assert [item.project_id for item in repository.list()] == sorted(identifiers)


def test_frontend_contracts_are_explicit_and_do_not_bypass_typed_clients() -> None:
    """Designer, monitor, and chat remain side-effect-free frontend contracts."""
    root = Path(__file__).resolve().parents[3] / "studio" / "frontend" / "src"
    sources = {
        "designer": (root / "workflow.ts").read_text(encoding="utf-8"),
        "monitor": (root / "features" / "executions" / "store.ts").read_text(
            encoding="utf-8"
        ),
        "chat": (root / "features" / "chat" / "store.ts").read_text(encoding="utf-8"),
    }
    assert "toWorkflowPayload" in sources["designer"]
    assert "snapshot" in sources["designer"]
    assert "loadExecutions" in sources["monitor"]
    assert "setInterval" not in sources["monitor"]
    assert "sendMessage" in sources["chat"]
    assert "AgentSDKAdapter" in sources["chat"]
    for source in sources.values():
        assert "fetch(" not in source
        assert "setInterval" not in source


def test_sdk_examples_and_reference_fixture_sources_are_offline(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Reference SDK examples run deterministically without credentials or network."""
    root = Path(__file__).resolve().parents[3]
    for name in ("basic_agent.py", "agent_with_memory.py", "streaming_agent.py"):
        runpy.run_path(str(root / "examples" / "sdk" / name))
    captured = capsys.readouterr().out
    assert "hello" in captured
    fixtures = (
        root / "studio" / "frontend" / "src" / "features" / "chat" / "fixtures.ts"
    ).read_text(encoding="utf-8")
    assert "referenceConversation" in fixtures and "reference-execution" in fixtures


def test_studio_documentation_links_cover_the_reference_product_layers() -> None:
    """The RC baseline keeps Studio's product and release documentation discoverable."""
    root = Path(__file__).resolve().parents[3]
    for name in (
        "Studio.md",
        "REST_API.md",
        "Frontend.md",
        "WorkflowDesigner.md",
        "ExecutionMonitor.md",
        "AgentChat.md",
        "SDK.md",
    ):
        assert (root / "docs" / name).is_file()
    studio = (root / "docs" / "Studio.md").read_text(encoding="utf-8")
    for link in ("WorkflowDesigner.md", "ExecutionMonitor.md", "AgentChat.md"):
        assert link in studio
