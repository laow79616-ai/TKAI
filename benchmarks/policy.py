"""Offline Policy Engine benchmarks using compact deterministic policy objects."""

from __future__ import annotations

from benchmarks import BenchmarkReport, BenchmarkResult, BenchmarkRunner
from tkai.policy import PolicyContext, PolicyDecision, PolicyManager, PolicyStage


class _StaticPolicy:
    def __init__(self, name: str, allowed: bool) -> None:
        self._name = name
        self._allowed = allowed

    def name(self) -> str:
        return self._name

    def priority(self) -> int:
        return 0

    def enabled(self) -> bool:
        return True

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        del context
        return PolicyDecision(self._allowed, "allowed" if self._allowed else "denied")

    def apply(self, context: PolicyContext) -> None:
        context.data["policy_applied"] = self._name

    def shutdown(self) -> None:
        return None


def _manager(allowed: bool | None) -> tuple[PolicyManager, PolicyContext]:
    manager = PolicyManager()
    if allowed is not None:
        manager.register(_StaticPolicy("benchmark", allowed))
    return manager, PolicyContext(PolicyStage.BEFORE_REQUEST)


def benchmark_allowed(iterations: int = 10) -> BenchmarkResult:
    manager, context = _manager(True)
    return BenchmarkRunner(iterations=iterations, random_seed=17).run(
        lambda: manager.execute(context)
    )


def benchmark_rejected(iterations: int = 10) -> BenchmarkResult:
    manager, context = _manager(False)
    return BenchmarkRunner(iterations=iterations, random_seed=17).run(
        lambda: manager.execute(context)
    )


def benchmark_default(iterations: int = 10) -> BenchmarkResult:
    manager, context = _manager(None)
    return BenchmarkRunner(iterations=iterations, random_seed=17).run(
        lambda: manager.execute(context)
    )


def run_benchmark(iterations: int = 10) -> BenchmarkResult:
    return benchmark_allowed(iterations)


if __name__ == "__main__":
    BenchmarkReport.emit("policy.allowed", run_benchmark())
