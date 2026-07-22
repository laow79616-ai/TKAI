"""Provider-local retry policy independent of workflow execution."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import TypeVar

from .errors import ProviderResponseError, ProviderTimeoutError, RateLimitError

T = TypeVar("T")


def parse_retry_after(
    value: str | None,
    *,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> float | None:
    """Parse Retry-After seconds or HTTP date without raising on invalid input."""
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        target = parsedate_to_datetime(value)
        if target.tzinfo is None:
            target = target.replace(tzinfo=timezone.utc)
        return max(0.0, (target - clock()).total_seconds())
    except (TypeError, ValueError):
        return None


def retry_call(
    operation: Callable[[], T],
    *,
    max_retries: int = 0,
    sleep: Callable[[float], None] = lambda _: None,
    random: Callable[[], float] = lambda: 0.0,
    retry_after: float | None = None,
) -> T:
    """Retry only transient provider failures with deterministic injectable hooks."""
    for attempt in range(max_retries + 1):
        try:
            return operation()
        except (ProviderTimeoutError, RateLimitError, ProviderResponseError):
            if attempt == max_retries:
                raise
            sleep(retry_after if retry_after is not None else (2**attempt) + random())
    raise AssertionError("unreachable")
