"""Offline Studio RC-2 benchmarks for local reference paths, not performance gates."""

from __future__ import annotations

import json
from collections.abc import Callable

from studio.backend import SDKStudioGateway, StudioDependencies
from studio.backend.api import StudioAPI
from tkai.sdk.workflow import Node, WorkflowBuilder, WorkflowRuntime

from .base import BenchmarkRunner
from .models import BenchmarkResult
from .report import BenchmarkReport


def _runner(iterations: int) -> BenchmarkRunner:
    """Create the bounded, fixed-seed runner used by every Studio scenario."""
    return BenchmarkRunner(warmup=1, iterations=iterations, random_seed=2_100)


def _dependencies() -> StudioDependencies:
    """Compose a fully local Studio host with an explicitly injected SDK runtime."""
    definition = WorkflowBuilder("benchmark").add(Node("task", handler="ok")).build()
    return StudioDependencies.create(
        sdk_gateway=SDKStudioGateway(workflow_runtime=WorkflowRuntime(definition))
    )


def benchmark_backend(iterations: int = 10) -> BenchmarkResult:
    """Measure a read-only local Studio health/system controller path."""
    api = StudioAPI(_dependencies())
    return _runner(iterations).run(lambda: (api.health(), api.system(), api.version()))


def benchmark_rest(iterations: int = 10) -> BenchmarkResult:
    """Measure frozen controller create/get/list work without starting FastAPI."""
    api = StudioAPI(_dependencies())
    api.create_project({"project_id": "project", "name": "Project"})
    api.create_workflow(
        {"workflow_id": "workflow", "project_id": "project", "name": "Workflow"}
    )
    return _runner(iterations).run(
        lambda: (api.get_project("project"), api.list_workflows())
    )


def benchmark_designer(iterations: int = 10) -> BenchmarkResult:
    """Measure deterministic serializable Designer reference-payload handling."""
    payload = {
        "workflow_id": "reference-chat",
        "project_id": "reference",
        "name": "Simple Chat Flow",
        "nodes": [{"node_id": "task", "kind": "task", "label": "Task"}],
        "edges": [],
        "metadata": {"version": "1"},
    }
    return _runner(iterations).run(
        lambda: json.loads(json.dumps(payload, sort_keys=True))
    )


def benchmark_execution_monitor(iterations: int = 10) -> BenchmarkResult:
    """Measure deterministic serialization of an explicit monitor reference snapshot."""
    snapshot = {
        "execution_id": "reference-execution",
        "status": "completed",
        "timeline": [{"id": "done", "type": "execution_completed"}],
        "metrics": {"provider_call_count": 1, "memory_operation_count": 1},
    }
    return _runner(iterations).run(
        lambda: json.loads(json.dumps(snapshot, sort_keys=True))
    )


def benchmark_agent_chat(iterations: int = 10) -> BenchmarkResult:
    """Measure deterministic local conversation/reference-memory serialization."""
    conversation = {
        "id": "reference-chat",
        "session_id": "reference-session",
        "messages": [{"role": "user", "content": "hello"}],
        "memory": {"context": []},
    }
    return _runner(iterations).run(
        lambda: json.loads(json.dumps(conversation, sort_keys=True))
    )


def benchmark_sdk_gateway(iterations: int = 10) -> BenchmarkResult:
    """Measure the explicit Studio-to-public-SDK workflow gateway boundary."""
    gateway = _dependencies().sdk_gateway
    return _runner(iterations).run(gateway.execute_workflow)


def benchmark_repository(iterations: int = 10) -> BenchmarkResult:
    """Measure stable local repository reads after explicit setup."""
    dependencies = _dependencies()
    dependencies.project_service.create("Project", project_id="project")
    return _runner(iterations).run(dependencies.project_repository.list)


def benchmark_service(iterations: int = 10) -> BenchmarkResult:
    """Measure a deterministic local project-service list path."""
    dependencies = _dependencies()
    dependencies.project_service.create("Project", project_id="project")
    return _runner(iterations).run(dependencies.project_service.list)


STUDIO_BENCHMARKS: tuple[tuple[str, Callable[[int], BenchmarkResult]], ...] = (
    ("studio_backend", benchmark_backend),
    ("studio_rest", benchmark_rest),
    ("studio_workflow_designer", benchmark_designer),
    ("studio_execution_monitor", benchmark_execution_monitor),
    ("studio_agent_chat", benchmark_agent_chat),
    ("studio_sdk_gateway", benchmark_sdk_gateway),
    ("studio_repository", benchmark_repository),
    ("studio_service", benchmark_service),
)


def run_benchmark(iterations: int = 10) -> BenchmarkResult:
    """Provide the normal module entry point with the SDK gateway scenario."""
    return benchmark_sdk_gateway(iterations)


if __name__ == "__main__":
    BenchmarkReport.emit("studio.sdk_gateway", run_benchmark())
