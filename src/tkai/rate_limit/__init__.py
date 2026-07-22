"""Local, pluggable, EventBus-observable provider quota foundation."""

from .errors import QuotaNotFoundError, RateLimitError
from .events import QuotaConsumed, QuotaReset, RateLimitEvent, RateLimitExceeded
from .limiter import RateLimiter
from .manager import RateLimitManager
from .models import RateLimitSnapshot
from .registry import QuotaRegistry
from .strategy import (
    FixedWindowStrategy,
    RateLimitAwareStrategy,
    RateLimitStrategy,
    SlidingWindowStrategy,
    TokenBucketStrategy,
)

__all__ = (
    "FixedWindowStrategy",
    "QuotaConsumed",
    "QuotaNotFoundError",
    "QuotaRegistry",
    "QuotaReset",
    "RateLimitAwareStrategy",
    "RateLimitError",
    "RateLimitEvent",
    "RateLimitExceeded",
    "RateLimitManager",
    "RateLimitSnapshot",
    "RateLimitStrategy",
    "RateLimiter",
    "SlidingWindowStrategy",
    "TokenBucketStrategy",
)
