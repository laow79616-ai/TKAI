"""Offline TKAI 2.0 SDK benchmarks with structural, not threshold, validation."""

from __future__ import annotations

from collections.abc import Callable

from tkai.sdk import Agent
from tkai.sdk.adapters import InMemoryProvider, ProviderAdapter, V1RuntimeAdapter
from tkai.sdk.memory import MemoryRecord, ReferenceMemory
from tkai.sdk.plugins.runtime import EchoPlugin, PluginContext, PluginRuntime
from tkai.sdk.provider import ProviderRequest, ReferenceProvider
from tkai.sdk.tools import EchoTool, ToolRequest
from tkai.sdk.workflow import Node, WorkflowDefinition, WorkflowRuntime

from .base import BenchmarkRunner
from .models import BenchmarkResult


def _runner(iterations: int) -> BenchmarkRunner:
    """Build a fixed-seed, bounded runner shared by all SDK scenarios."""
    return BenchmarkRunner(warmup=1, iterations=iterations, random_seed=2_000)


def benchmark_agent(iterations: int = 10) -> BenchmarkResult:
    """Measure one explicit Agent-to-reference-adapter chat path."""
    agent = Agent(V1RuntimeAdapter(ProviderAdapter(InMemoryProvider())))
    return _runner(iterations).run(lambda: agent.chat("benchmark"))


def benchmark_workflow(iterations: int = 10) -> BenchmarkResult:
    """Measure bounded local reference workflow execution."""
    runtime = WorkflowRuntime(
        WorkflowDefinition("benchmark", (Node("task", handler="ok"),), "task")
    )
    return _runner(iterations).run(runtime.execute)


def benchmark_tool(iterations: int = 10) -> BenchmarkResult:
    """Measure a deterministic local Reference Tool invocation."""
    tool = EchoTool()
    request = ToolRequest("echo", {"value": "benchmark"})
    return _runner(iterations).run(lambda: tool.execute(request))


def benchmark_provider(iterations: int = 10) -> BenchmarkResult:
    """Measure the vendor-neutral offline reference provider path."""
    provider = ReferenceProvider()
    request = ProviderRequest("benchmark")
    return _runner(iterations).run(lambda: provider.execute(request))


def benchmark_memory(iterations: int = 10) -> BenchmarkResult:
    """Measure bounded reference-memory overwrite/store behavior."""
    memory = ReferenceMemory()
    record = MemoryRecord("benchmark", "value")
    return _runner(iterations).run(lambda: memory.store(record))


def benchmark_plugin(iterations: int = 10) -> BenchmarkResult:
    """Measure one explicitly enabled local reference-plugin execution."""
    runtime = PluginRuntime()
    plugin = EchoPlugin()
    runtime.load(plugin)
    runtime.initialize(plugin.manifest.name, PluginContext())
    runtime.enable(plugin.manifest.name)
    return _runner(iterations).run(lambda: runtime.execute(plugin.manifest.name, "ok"))


def benchmark_runtime_adapter(iterations: int = 10) -> BenchmarkResult:
    """Measure the explicit V1-compatible reference Runtime Adapter path."""
    adapter = V1RuntimeAdapter(ProviderAdapter(InMemoryProvider()))
    agent = Agent(adapter)
    return _runner(iterations).run(lambda: agent.run("benchmark"))


SDK_BENCHMARKS: tuple[tuple[str, Callable[[int], BenchmarkResult]], ...] = (
    ("sdk_agent", benchmark_agent),
    ("sdk_workflow", benchmark_workflow),
    ("sdk_tool", benchmark_tool),
    ("sdk_provider", benchmark_provider),
    ("sdk_memory", benchmark_memory),
    ("sdk_plugin", benchmark_plugin),
    ("sdk_runtime_adapter", benchmark_runtime_adapter),
)
