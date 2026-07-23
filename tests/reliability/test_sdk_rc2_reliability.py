"""Offline lifecycle, cleanup, failure, retry, and snapshot validation for SDK RC-2."""

from __future__ import annotations

import gc
import tracemalloc
import weakref

import pytest

from tkai.sdk import Agent
from tkai.sdk.adapters import InMemoryProvider, ProviderAdapter, V1RuntimeAdapter
from tkai.sdk.errors import ProviderExecutionError
from tkai.sdk.memory import MemoryLifecycleError, MemoryRecord, ReferenceMemory
from tkai.sdk.plugins.runtime import EchoPlugin, PluginContext, PluginRuntime
from tkai.sdk.provider import ProviderLifecycleError, ProviderRequest, ReferenceProvider
from tkai.sdk.tools import MathTool, ToolRequest, ToolStatus
from tkai.sdk.workflow import (
    Node,
    NodeKind,
    WorkflowDefinition,
    WorkflowRuntime,
    WorkflowState,
)


def test_sdk_failures_are_isolated_and_retry_exhaustion_is_bounded() -> None:
    """A failure in each local component does not corrupt a fresh reference object."""
    failing = Agent(
        V1RuntimeAdapter(
            ProviderAdapter(InMemoryProvider(responder=lambda _request: 1 / 0))
        )
    )
    with pytest.raises(ProviderExecutionError):
        failing.chat("failure")
    assert (
        Agent(V1RuntimeAdapter(ProviderAdapter(InMemoryProvider()))).chat("ok").output
        == "ok"
    )

    assert (
        MathTool()
        .execute(ToolRequest("math", {"operation": "invalid", "left": 1, "right": 2}))
        .status
        is ToolStatus.ERROR
    )
    attempts = 0

    def fail(_context: object) -> object:
        nonlocal attempts
        attempts += 1
        raise RuntimeError("retry exhausted")

    workflow = WorkflowRuntime(
        WorkflowDefinition(
            "retry",
            (Node("retry", NodeKind.RETRY, fail, metadata={"attempts": 3}),),
            "retry",
        )
    )
    assert workflow.execute().state is WorkflowState.FAILED
    assert attempts == 3


def test_sdk_snapshot_cleanup_and_reference_lifecycle_release_local_state() -> None:
    """Snapshots are defensive and close/shutdown release bounded local references."""
    tracemalloc.start()
    try:
        memory = ReferenceMemory()
        memory.store(MemoryRecord("key", {"nested": [1]}))
        snapshot = memory.snapshot()
        assert snapshot.records[0].value == {"nested": [1]}
        snapshot.records[0].value["nested"].append(2)
        assert memory.get("key").value == {"nested": [1]}

        plugin = EchoPlugin()
        plugin_ref = weakref.ref(plugin)
        runtime = PluginRuntime()
        runtime.load(plugin)
        runtime.initialize(plugin.manifest.name, PluginContext(memory=memory))
        runtime.enable(plugin.manifest.name)
        runtime.shutdown()
        memory.close()
        with pytest.raises(MemoryLifecycleError):
            memory.snapshot()
        del plugin
        gc.collect()
        assert plugin_ref() is None
        current, _peak = tracemalloc.get_traced_memory()
        assert current >= 0
    finally:
        tracemalloc.stop()


def test_provider_close_and_plugin_failure_cleanup_do_not_escape_context() -> None:
    """Local closes and plugin work leave independent contexts usable."""
    provider = ReferenceProvider()
    provider.close()
    with pytest.raises(ProviderLifecycleError):
        provider.execute(ProviderRequest("closed"))
    assert ReferenceProvider().execute(ProviderRequest("new")).output == "new"

    runtime = PluginRuntime()
    plugin = EchoPlugin()
    runtime.load(plugin)
    runtime.initialize(plugin.manifest.name, PluginContext())
    runtime.enable(plugin.manifest.name)
    assert runtime.execute(plugin.manifest.name, "value") == "value"
    runtime.shutdown()
