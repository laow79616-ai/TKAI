"""Bounded concurrent offline stress validation for TKAI 2.0 SDK references."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import enumerate as active_threads

from tkai.sdk import Agent
from tkai.sdk.adapters import InMemoryProvider, ProviderAdapter, V1RuntimeAdapter
from tkai.sdk.memory import MemoryRecord, ReferenceMemory
from tkai.sdk.plugins.runtime import EchoPlugin, PluginContext, PluginRuntime
from tkai.sdk.provider import ProviderRequest, ReferenceProvider
from tkai.sdk.tools import EchoTool, ToolRequest
from tkai.sdk.workflow import Node, WorkflowDefinition, WorkflowRuntime, WorkflowState


def test_sdk_reference_components_remain_consistent_under_bounded_concurrency() -> None:
    """Bounded SDK reference calls share no corrupt local state."""
    before = {thread.ident for thread in active_threads()}
    agent = Agent(V1RuntimeAdapter(ProviderAdapter(InMemoryProvider())))
    workflow = WorkflowRuntime(
        WorkflowDefinition("stress", (Node("task", handler="workflow"),), "task")
    )
    memory = ReferenceMemory()
    tool = EchoTool()
    provider = ReferenceProvider()
    plugins = PluginRuntime()
    plugin = EchoPlugin()
    plugins.load(plugin)
    plugins.initialize(plugin.manifest.name, PluginContext())
    plugins.enable(plugin.manifest.name)

    def operate(index: int) -> tuple[object, ...]:
        memory.store(MemoryRecord(str(index), index))
        return (
            agent.chat(index).output,
            workflow.execute().state,
            tool.execute(ToolRequest("echo", {"value": index})).output,
            provider.execute(ProviderRequest(index)).output,
            plugins.execute(plugin.manifest.name, index),
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(operate, range(48)))

    assert all(result[1] is WorkflowState.SUCCEEDED for result in results)
    assert len(memory.snapshot().records) == 48
    assert {thread.ident for thread in active_threads()} <= before


def test_plugin_lifecycle_concurrency_is_serialized_without_duplicate_state() -> None:
    """Independent runtimes can perform explicit lifecycle actions without deadlock."""

    def lifecycle(index: int) -> str:
        runtime = PluginRuntime()
        plugin = EchoPlugin(f"plugin-{index}")
        runtime.load(plugin)
        runtime.initialize(plugin.manifest.name, PluginContext())
        runtime.enable(plugin.manifest.name)
        assert runtime.execute(plugin.manifest.name, "ok") == "ok"
        runtime.shutdown()
        return plugin.manifest.name

    with ThreadPoolExecutor(max_workers=8) as executor:
        names = list(executor.map(lifecycle, range(32)))
    assert sorted(names) == sorted(f"plugin-{index}" for index in range(32))
