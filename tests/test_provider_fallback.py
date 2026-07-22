"""Offline tests for the standalone provider fallback policy engine."""

from __future__ import annotations

import pytest

from tkai.ai import (
    AuthenticationError,
    FallbackCandidate,
    FallbackEngine,
    FallbackExhaustedError,
    FallbackPolicy,
    ProviderTimeoutError,
)


def candidates() -> list[FallbackCandidate[str]]:
    """Return a stable candidate list comparable to capability-router output."""
    return [
        FallbackCandidate("first", "first"),
        FallbackCandidate("second", "second"),
        FallbackCandidate("third", "third"),
    ]


def test_first_second_and_third_candidate_can_each_succeed() -> None:
    for successful in ("first", "second", "third"):
        calls: list[str] = []

        def operation(
            candidate: str,
            expected: str = successful,
            recorded_calls: list[str] = calls,
        ) -> str:
            recorded_calls.append(candidate)
            if candidate != expected:
                raise AuthenticationError("invalid credentials")
            return candidate

        assert (
            FallbackEngine(FallbackPolicy(max_attempts=3)).execute(
                candidates(), operation
            )
            == successful
        )
        assert calls[-1] == successful


def test_temporary_failure_retries_the_same_candidate_within_budget() -> None:
    calls: list[str] = []

    def operation(candidate: str) -> str:
        calls.append(candidate)
        if len(calls) == 1:
            raise ProviderTimeoutError("temporary")
        return candidate

    result = FallbackEngine(FallbackPolicy(max_attempts=3, retry_budget=1)).execute(
        candidates(), operation
    )

    assert result == "first"
    assert calls == ["first", "first"]


def test_permanent_failure_advances_without_retry() -> None:
    calls: list[str] = []

    def operation(candidate: str) -> str:
        calls.append(candidate)
        if candidate == "first":
            raise AuthenticationError("do not retry")
        return candidate

    assert (
        FallbackEngine(FallbackPolicy(max_attempts=3, retry_budget=2)).execute(
            candidates(), operation
        )
        == "second"
    )
    assert calls == ["first", "second"]


def test_retry_budget_and_max_attempts_bound_failover() -> None:
    calls: list[str] = []

    def operation(candidate: str) -> str:
        calls.append(candidate)
        raise ProviderTimeoutError("temporary")

    with pytest.raises(FallbackExhaustedError) as error:
        FallbackEngine(FallbackPolicy(max_attempts=3, retry_budget=1)).execute(
            candidates(), operation
        )

    assert calls == ["first", "first", "second"]
    assert error.value.attempted_providers == ("first", "first", "second")


def test_blacklist_preserves_remaining_candidate_order() -> None:
    engine = FallbackEngine(FallbackPolicy(blocked_providers=frozenset({"second"})))
    engine.blacklist("first")

    names = [candidate.name for candidate in engine.ordered_candidates(candidates())]
    assert names == ["third"]
    engine.unblacklist("first")
    names = [candidate.name for candidate in engine.ordered_candidates(candidates())]
    assert names == ["first", "third"]


def test_candidate_exhaustion_keeps_only_safe_failure_summaries() -> None:
    secret = "Bearer this-must-not-appear"

    def operation(candidate: str) -> str:
        raise ProviderTimeoutError(secret)

    with pytest.raises(FallbackExhaustedError) as error:
        FallbackEngine(FallbackPolicy(max_attempts=3)).execute(candidates(), operation)

    assert "ProviderTimeoutError" in str(error.value)
    assert secret not in str(error.value)


def test_streaming_fallback_is_allowed_before_the_first_business_item() -> None:
    calls: list[str] = []

    def stream(candidate: str):
        calls.append(candidate)
        if candidate == "first":
            raise ProviderTimeoutError("before output")
        yield "second output"

    engine = FallbackEngine(FallbackPolicy(max_attempts=3))
    assert list(engine.stream(candidates(), stream)) == ["second output"]
    assert calls == ["first", "second"]


def test_streaming_never_falls_back_after_the_first_business_item() -> None:
    calls: list[str] = []

    def stream(candidate: str):
        calls.append(candidate)
        yield "visible"
        raise ProviderTimeoutError("after output")

    engine = FallbackEngine(FallbackPolicy(max_attempts=3))
    iterator = engine.stream(candidates(), stream)
    assert next(iterator) == "visible"
    with pytest.raises(ProviderTimeoutError):
        next(iterator)
    assert calls == ["first"]
