"""Offline bounded retry classification, budget, and decision benchmarks."""

from __future__ import annotations

from benchmarks import BenchmarkReport, BenchmarkResult, BenchmarkRunner
from tkai.retry import RetryManager, RetryPolicy


def benchmark_retryable_decision(iterations: int = 10) -> BenchmarkResult:
    policy = RetryPolicy("benchmark", max_attempts=3)
    budget = policy.budget()
    return BenchmarkRunner(iterations=iterations, random_seed=17).run(
        lambda: policy.decide(TimeoutError("offline"), 1, budget)
    )


def benchmark_non_retryable_decision(iterations: int = 10) -> BenchmarkResult:
    policy = RetryPolicy("benchmark", max_attempts=3)
    return BenchmarkRunner(iterations=iterations, random_seed=17).run(
        lambda: policy.decide(ValueError("local"), 1, policy.budget())
    )


def benchmark_budget_limit(iterations: int = 10) -> BenchmarkResult:
    policy = RetryPolicy("benchmark", max_attempts=2)
    return BenchmarkRunner(iterations=iterations, random_seed=17).run(
        lambda: policy.decide(TimeoutError("offline"), 2, policy.budget().consume())
    )


def benchmark_manager_path(iterations: int = 10) -> BenchmarkResult:
    manager = RetryManager()
    manager.register(RetryPolicy("benchmark", max_attempts=1))
    return BenchmarkRunner(iterations=iterations, random_seed=17).run(
        lambda: manager.run(lambda: "ok", policy="benchmark")
    )


def run_benchmark(iterations: int = 10) -> BenchmarkResult:
    return benchmark_retryable_decision(iterations)


if __name__ == "__main__":
    BenchmarkReport.emit("retry.retryable", run_benchmark())
