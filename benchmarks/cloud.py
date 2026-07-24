"""Offline Cloud RC-2 benchmarks for reference foundations only."""

from __future__ import annotations

from collections.abc import Callable

from cloud.deployment import ReferenceDeploymentService
from cloud.execution import ReferenceExecutionService
from cloud.gateway import GatewayCapability, ReferencePlatformGateway
from cloud.project import ReferenceProjectService
from cloud.storage import ReferenceStorageService
from cloud.workspace import ReferenceWorkspaceService

from .base import BenchmarkRunner
from .models import BenchmarkResult
from .report import BenchmarkReport


def _runner(iterations: int) -> BenchmarkRunner:
    """Create the bounded fixed-seed runner shared by Cloud scenarios."""
    return BenchmarkRunner(warmup=1, iterations=iterations, random_seed=4_200)


def benchmark_workspace(iterations: int = 10) -> BenchmarkResult:
    """Measure a stable local workspace lookup and snapshot."""
    service = ReferenceWorkspaceService()
    service.create("workspace", "account", "Workspace")
    return _runner(iterations).run(
        lambda: (service.workspace("workspace"), service.workspaces())
    )


def benchmark_project(iterations: int = 10) -> BenchmarkResult:
    """Measure a stable local project lookup and snapshot."""
    service = ReferenceProjectService()
    service.create("project", "workspace", "Project")
    return _runner(iterations).run(
        lambda: (service.project("project"), service.projects())
    )


def benchmark_deployment(iterations: int = 10) -> BenchmarkResult:
    """Measure a stable local deployment lookup and snapshot."""
    service = ReferenceDeploymentService()
    service.create("deployment", "project", "workspace", "Deployment")
    return _runner(iterations).run(
        lambda: (service.get("deployment"), service.snapshot())
    )


def benchmark_storage(iterations: int = 10) -> BenchmarkResult:
    """Measure a stable local storage descriptor lookup and snapshot."""
    service = ReferenceStorageService()
    service.registry.register(
        service.factory.storage("storage", "project", "workspace", "Storage")
    )
    return _runner(iterations).run(lambda: (service.get("storage"), service.snapshot()))


def benchmark_execution(iterations: int = 10) -> BenchmarkResult:
    """Measure a stable local execution lookup and snapshot."""
    service = ReferenceExecutionService()
    service.create("execution", "deployment", "project", "workspace")
    return _runner(iterations).run(
        lambda: (service.get("execution"), service.snapshot())
    )


def benchmark_gateway(iterations: int = 10) -> BenchmarkResult:
    """Measure the explicit read-only Platform Gateway boundary."""
    gateway = ReferencePlatformGateway((GatewayCapability("cloud"),))
    return _runner(iterations).run(
        lambda: (gateway.capabilities(), gateway.version(), gateway.health())
    )


CLOUD_BENCHMARKS: tuple[tuple[str, Callable[[int], BenchmarkResult]], ...] = (
    ("cloud_workspace", benchmark_workspace),
    ("cloud_project", benchmark_project),
    ("cloud_deployment", benchmark_deployment),
    ("cloud_storage", benchmark_storage),
    ("cloud_execution", benchmark_execution),
    ("cloud_gateway", benchmark_gateway),
)


def run_benchmark(iterations: int = 10) -> BenchmarkResult:
    """Provide the normal module entry point with the gateway scenario."""
    return benchmark_gateway(iterations)


if __name__ == "__main__":
    BenchmarkReport.emit("cloud.gateway", run_benchmark())
