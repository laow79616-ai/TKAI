"""Concurrent local Retry Framework validation without delays or provider calls."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from tkai.retry import RetryManager, RetryPolicy


def test_retry_manager_concurrently_records_bounded_failure_paths() -> None:
    """Every operation exhausts independently and retains expected event records."""
    operations = 48
    manager = RetryManager()
    policy = RetryPolicy("bounded", max_attempts=2)

    def fail() -> None:
        raise TimeoutError("offline")

    def exercise(_number: int) -> None:
        with pytest.raises(TimeoutError):
            manager.run(fail, policy=policy)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(exercise, number) for number in range(operations)]
        for future in futures:
            future.result(timeout=10)

    assert len(manager.events) == operations * 2
    assert sum(event.name == "RetryScheduled" for event in manager.events) == operations
    assert sum(event.name == "RetryExhausted" for event in manager.events) == operations


def test_retry_policy_permanent_failure_never_consumes_operation_budget() -> None:
    """The immutable budget remains unchanged when classification rejects a retry."""
    policy = RetryPolicy("permanent", max_attempts=3)
    budget = policy.budget()
    decision = policy.decide(ValueError("invalid"), 1, budget)
    assert not decision.retry
    assert budget.consumed == 0
