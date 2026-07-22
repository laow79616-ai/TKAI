"""Provider-local retry policy independent of workflow execution."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from .errors import ProviderResponseError, ProviderTimeoutError, RateLimitError

T = TypeVar("T")


def retry_call(
    operation: Callable[[], T],
    *,
    max_retries: int = 0,
    sleep: Callable[[float], None] = lambda _: None,
    random: Callable[[], float] = lambda: 0.0,
) -> T:
    """Retry only transient provider failures with deterministic injectable hooks."""
    for attempt in range(max_retries + 1):
        try:
            return operation()
        except (ProviderTimeoutError, RateLimitError, ProviderResponseError):
            if attempt == max_retries:
                raise
            sleep((2**attempt) + random())
    raise AssertionError("unreachable")
