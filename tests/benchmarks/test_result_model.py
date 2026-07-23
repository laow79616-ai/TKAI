"""Immutable and safe BenchmarkResult serialization tests."""

import json
from dataclasses import FrozenInstanceError

import pytest

from benchmarks import BenchmarkResult, BenchmarkRunner


def test_result_is_frozen_and_json_safe() -> None:
    result = BenchmarkResult(operations=2, elapsed_seconds=1.0, ops_per_second=2.0)
    with pytest.raises(FrozenInstanceError):
        result.operations = 3  # type: ignore[misc]
    assert result.to_dict()["operations"] == 2
    assert json.loads(result.to_json())["ops_per_second"] == 2.0


def test_empty_benchmark_and_fixed_seed_are_safe_and_repeatable() -> None:
    assert (
        BenchmarkRunner(iterations=0, repeats=0).run(lambda: None) == BenchmarkResult()
    )
    values: list[float] = []

    def operation() -> None:
        import random

        values.append(random.random())

    runner = BenchmarkRunner(iterations=3, repeats=2, random_seed=17)
    runner.run(operation)
    first = list(values)
    values.clear()
    runner.run(operation)
    assert values == first
