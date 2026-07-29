"""Offline TKAI 2.0 RC-1 integration, lifecycle, isolation, and example checks."""

from __future__ import annotations

import runpy
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from tkai.sdk import Agent
from tkai.sdk.adapters import InMemoryProvider, ProviderAdapter, V1RuntimeAdapter
from tkai.sdk.errors import ProviderExecutionError
from tkai.sdk.memory import MemoryRecord, ReferenceMemory
from tkai.sdk.plugins.runtime import (
    MemoryPlugin,
    PluginContext,
    PluginLifecycle,
    PluginRuntime,
    WorkflowPlugin,
)
from tkai.sdk.provider import ProviderLifecycleError, ProviderRequest, ReferenceProvider
from tkai.sdk.tools import EchoTool, MathTool, ToolRequest, ToolStatus
from tkai.sdk.workflow import Node, WorkflowDefinition, WorkflowRuntime, WorkflowState


def _agent() -> Agent:
    """Build the explicit local V1-runtime adapter path used by all Agent calls."""
    return Agent(V1RuntimeAdapter(ProviderAdapter(InMemoryProvider())))


def test_sdk_chain_covers_agent_workflow_tool_provider_memory_and_plugins() -> None:
    """The complete SDK reference chain is explicit, deterministic, and offline."""
    agent = _agent()
    assert agent.chat("chat").output == "chat"
    assert agent.run("run").output == "run"
    assert agent.call("named", "call").metadata["call"] == "named"
    assert [item.output for item in agent.stream("stream")] == ["stream"]

    provider = ReferenceProvider()
    assert provider.execute(ProviderRequest("provider")).output == "provider"
    assert [chunk.finished for chunk in provider.stream(ProviderRequest("stream"))] == [
        False,
        True,
    ]

    memory = ReferenceMemory()
    memory.store(MemoryRecord("note", "memory"))
    tool = EchoTool()
    workflow = WorkflowRuntime(
        WorkflowDefinition(
            "integration",
            (
                Node(
                    "agent",
                    handler=lambda _context: agent.chat("workflow").output,
                    successors=("tool",),
                ),
                Node(
                    "tool",
                    handler=lambda _context: (
                        tool.execute(ToolRequest("echo", {"value": "tool"})).output
                    ),
                ),
            ),
            "agent",
        )
    )
    plugins = PluginRuntime()
    workflow_plugin = WorkflowPlugin()
    memory_plugin = MemoryPlugin()
    for plugin, context in (
        (workflow_plugin, PluginContext(workflow=workflow)),
        (memory_plugin, PluginContext(memory=memory)),
    ):
        plugins.load(plugin)
        plugins.initialize(plugin.manifest.name, context)
        plugins.enable(plugin.manifest.name)

    assert plugins.execute(workflow_plugin.manifest.name).output == "tool"
    assert plugins.execute(memory_plugin.manifest.name, "note") == "memory"


def test_failure_isolation_and_lifecycle_keep_independent_sdk_objects_usable() -> None:
    """Reference failures remain local and later independent operations still work."""
    failing = Agent(
        V1RuntimeAdapter(
            ProviderAdapter(InMemoryProvider(responder=lambda _request: 1 / 0))
        )
    )
    with pytest.raises(ProviderExecutionError):
        failing.chat("fails")
    assert _agent().chat("recovered").output == "recovered"

    assert (
        MathTool()
        .execute(ToolRequest("math", {"operation": "unknown", "left": 1, "right": 2}))
        .status
        is ToolStatus.ERROR
    )
    assert (
        EchoTool().execute(ToolRequest("echo", {"value": "still-local"})).output
        == "still-local"
    )

    failed_workflow = WorkflowRuntime(
        WorkflowDefinition("bad", (Node("bad", handler=lambda _context: 1 / 0),), "bad")
    )
    assert failed_workflow.execute().state is WorkflowState.FAILED
    assert (
        WorkflowRuntime(
            WorkflowDefinition("good", (Node("good", handler="ok"),), "good")
        )
        .execute()
        .state
        is WorkflowState.SUCCEEDED
    )

    provider = ReferenceProvider()
    provider.close()
    with pytest.raises(ProviderLifecycleError):
        provider.execute(ProviderRequest("closed"))
    assert ReferenceProvider().execute(ProviderRequest("new")).output == "new"

    plugins = PluginRuntime()
    plugin = MemoryPlugin()
    plugins.load(plugin)
    plugins.initialize(plugin.manifest.name, PluginContext(memory=ReferenceMemory()))
    plugins.enable(plugin.manifest.name)
    assert plugins.disable(plugin.manifest.name) is PluginLifecycle.DISABLED
    plugins.shutdown()


def test_reference_registries_and_workflow_execution_are_thread_safe() -> None:
    """Bounded concurrent calls preserve the independent local SDK state model."""
    memory = ReferenceMemory()
    workflow = WorkflowRuntime(
        WorkflowDefinition("safe", (Node("task", handler="ok"),), "task")
    )
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(
            executor.map(
                lambda index: (
                    memory.store(MemoryRecord(str(index), index)),
                    workflow.execute().state,
                ),
                range(32),
            )
        )
    assert all(state is WorkflowState.SUCCEEDED for _, state in results)
    assert len(memory.snapshot().records) == 32


def test_sdk_examples_and_documentation_are_local_and_present() -> None:
    """Reference examples run without credentials, network access, or config."""
    root = Path(__file__).parents[2]
    for filename in ("basic_agent.py", "agent_with_memory.py", "streaming_agent.py"):
        runpy.run_path(root / "examples" / "sdk" / filename)
    for filename in (
        "SDK.md",
        "ProviderSDK.md",
        "MemorySDK.md",
        "WorkflowSDK.md",
        "ToolSDK.md",
        "PluginSDK.md",
    ):
        assert (root / "docs" / filename).is_file()
