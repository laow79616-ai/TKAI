"""Sprint-4 Enterprise Agent Runtime Foundation coverage."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from tkai.agent import (
    AgentApi,
    AgentCoordinator,
    AgentDefinition,
    AgentLimits,
    AgentRole,
    AgentRuntime,
    AgentStatus,
    CoordinationLimits,
    Delegation,
    MemoryNamespace,
    RegisteredTool,
    RetentionPolicy,
    RetryPolicy,
    ShortMemory,
    ToolDefinition,
    ToolRegistry,
)
from tkai.workflow import WorkflowEngine


def definition(identifier: str = "agent-1") -> AgentDefinition:
    return AgentDefinition(
        identifier,
        "Foundation Agent",
        "Local reference agent",
        "1.0.0",
        "Complete the assigned work.",
        tools=("search",),
        memory=("short",),
        permissions=("tool.search",),
        limits=AgentLimits(max_steps=4, timeout_seconds=10, max_tool_calls=2),
        metadata={"team": "platform"},
    )


def runtime() -> AgentRuntime:
    sequence = iter(("t1", "t2", "t3", "t4", "t5", "t6"))
    return AgentRuntime(
        clock=lambda: next(sequence),
        run_id_factory=lambda: "run-1",
    )


def test_definition_is_immutable_and_defensively_copied() -> None:
    metadata = {"team": "platform"}
    item = definition()
    metadata["team"] = "other"
    assert item.metadata["team"] == "platform"
    with pytest.raises(FrozenInstanceError):
        item.name = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        item.metadata["team"] = "changed"  # type: ignore[index]


def test_complete_lifecycle_and_audit_metrics() -> None:
    service = runtime()
    assert service.create(definition()).status is AgentStatus.DRAFT
    assert service.prepare("agent-1").status is AgentStatus.READY
    run = service.start_run("agent-1", "workspace-1", {"request": "test"})
    assert run.status is AgentStatus.RUNNING
    assert service.pause("run-1").status is AgentStatus.PAUSED
    assert service.resume("run-1").status is AgentStatus.RUNNING
    completed = service.complete("run-1", {"answer": 42}, duration_seconds=0.5)
    assert completed.status is AgentStatus.COMPLETED
    assert completed.outputs["answer"] == 42
    assert service.metrics.snapshot()["agent_success_total"] == 1
    assert [event.action.value for event in service.audit.list()] == [
        "create",
        "run",
        "pause",
        "resume",
    ]


def test_cancel_and_delete_are_audited_and_counted() -> None:
    service = runtime()
    service.create(definition())
    service.prepare("agent-1")
    service.start_run("agent-1", "workspace-1", {})
    service.delete_run("run-1")
    with pytest.raises(KeyError):
        service.get_run("run-1")
    assert service.metrics.snapshot()["agent_cancelled_total"] == 1
    assert [item.action.value for item in service.audit.list()][-2:] == [
        "cancel",
        "delete",
    ]


def test_illegal_lifecycle_transitions_are_rejected() -> None:
    service = runtime()
    service.create(definition())
    with pytest.raises(ValueError, match="Illegal agent transition"):
        service.transition("agent-1", AgentStatus.RUNNING)


def test_short_memory_namespaces_and_retention() -> None:
    memory = ShortMemory(RetentionPolicy(max_items=2))
    namespace = MemoryNamespace("agent-1/run-1")
    memory.put(namespace, "one", 1)
    memory.put(namespace, "two", 2)
    memory.put(namespace, "three", 3)
    assert memory.get(namespace, "one") is None
    assert memory.snapshot(namespace) == {"two": 2, "three": 3}
    assert memory.delete(namespace, "two")


def test_tool_registry_schema_permissions_and_duplicate_protection() -> None:
    registry = ToolRegistry()
    tool = RegisteredTool(
        ToolDefinition(
            "search",
            {"type": "object"},
            "tool.search",
            timeout_seconds=5,
            metadata={"owner": "platform"},
        ),
        lambda payload: payload["query"],
    )
    registry.register(tool)
    with pytest.raises(PermissionError):
        registry.get("search", ())
    assert registry.get("search", ("tool.search",)).handler({"query": "tkai"}) == "tkai"
    with pytest.raises(ValueError, match="already exists"):
        registry.register(tool)


def test_runtime_tool_invocation_enforces_assignment_retries_and_metrics() -> None:
    service = runtime()
    attempts = 0

    def handler(payload: Mapping[str, Any]) -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("retry")
        return str(payload)

    service.tools.register(
        RegisteredTool(
            ToolDefinition(
                "search",
                {"type": "object"},
                "tool.search",
                retry=RetryPolicy(attempts=2),
            ),
            handler,
        )
    )
    service.create(definition())
    service.prepare("agent-1")
    service.start_run("agent-1", "workspace-1", {})
    assert service.invoke_tool("run-1", "search", {"q": "tkai"})
    assert attempts == 2
    assert service.get_run("run-1").metrics.tool_calls == 1
    assert service.metrics.snapshot()["tool_calls_total"] == 1


def test_coordinator_roles_aggregation_cancellation_and_limits() -> None:
    coordinator = AgentCoordinator(
        CoordinationLimits(maximum_depth=2, maximum_agents=2, timeout_seconds=5)
    )
    delegations = (
        Delegation("lead", "planner", AgentRole.PLANNER, {"task": "plan"}),
        Delegation("lead", "reviewer", AgentRole.REVIEWER, {"task": "review"}),
    )
    result = coordinator.coordinate(delegations, lambda item: item.role.value)
    assert result.outputs == ("planner", "reviewer")
    cancelled = coordinator.coordinate(
        delegations, lambda item: item.role.value, cancelled=lambda: True
    )
    assert cancelled.cancelled and not cancelled.outputs
    with pytest.raises(ValueError, match="Maximum delegation depth"):
        coordinator.coordinate(
            (Delegation("a", "b", AgentRole.SUPPORT, depth=3),), lambda item: item
        )


def test_api_contract_create_list_run_get_delete() -> None:
    service = runtime()
    api = AgentApi(service)
    payload = definition().to_dict()
    assert api.create_agent(payload)["status"] == "draft"
    assert api.list_agents()["total"] == 1
    created = api.run_agent(
        {"agent_id": "agent-1", "workspace": "workspace-1", "inputs": {"x": 1}}
    )
    assert created["run_id"] == "run-1"
    assert api.get_run("run-1")["inputs"] == {"x": 1}
    assert api.delete_run("run-1") == {"deleted": True}


def test_metrics_prometheus_contract() -> None:
    service = runtime()
    service.metrics.increment("agent_runs_total")
    service.metrics.increment("tool_calls_total", 2)
    service.metrics.increment("tool_failures_total")
    service.metrics.observe_duration(0.25)
    output = service.metrics.render_prometheus()
    for name in (
        "agent_runs_total",
        "agent_success_total",
        "agent_failed_total",
        "agent_cancelled_total",
        "agent_duration_seconds",
        "tool_calls_total",
        "tool_failures_total",
    ):
        assert name in output


def test_architecture_reuses_workflow_runtime_and_preserves_boundaries() -> None:
    service = AgentRuntime()
    assert isinstance(service.workflow_engine, WorkflowEngine)
    root = Path(__file__).resolve().parents[2]
    runtime_source = (
        root / "src" / "tkai" / "agent" / "runtime" / "__init__.py"
    ).read_text(encoding="utf-8")
    assert "WorkflowEngine" in runtime_source
    assert "class Scheduler" not in runtime_source
    assert "class WorkflowRuntime" not in runtime_source


def test_required_package_and_dashboard_surfaces_exist() -> None:
    root = Path(__file__).resolve().parents[2]
    for package in (
        "runtime",
        "definition",
        "execution",
        "memory",
        "tools",
        "multi_agent",
        "models",
        "api",
    ):
        assert (root / "src" / "tkai" / "agent" / package / "__init__.py").is_file()
    dashboard = (root / "dashboard" / "frontend" / "src" / "App.tsx").read_text(
        encoding="utf-8"
    )
    assert "AgentDefinitionsPage" in dashboard
    assert "AgentRunsPage" in dashboard
    assert "AgentRunDetailsPage" in dashboard
