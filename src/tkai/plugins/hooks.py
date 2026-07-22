"""Stable failure-isolated hook names and dispatch ordering."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Any


class Hook(str, Enum):
    BEFORE_REQUEST = "BeforeRequest"
    AFTER_REQUEST = "AfterRequest"
    BEFORE_ROUTING = "BeforeRouting"
    AFTER_ROUTING = "AfterRouting"
    HEALTH_CHANGED = "HealthChanged"
    CACHE_HIT = "CacheHit"
    CACHE_MISS = "CacheMiss"
    RATE_LIMIT_EXCEEDED = "RateLimitExceeded"
    PROVIDER_SELECTED = "ProviderSelected"
    PROVIDER_FAILED = "ProviderFailed"


HookHandler = Callable[[dict[str, Any]], None]
