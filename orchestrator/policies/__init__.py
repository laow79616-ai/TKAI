"""Bounded execution policies."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    attempts: int = 3
    delay_seconds: float = 0


@dataclass(frozen=True, slots=True)
class TimeoutPolicy:
    seconds: float = 30


@dataclass(frozen=True, slots=True)
class ConcurrencyPolicy:
    maximum: int = 8


@dataclass(frozen=True, slots=True)
class RateLimitPolicy:
    executions: int = 100


@dataclass(frozen=True, slots=True)
class ExecutionPolicy:
    allowed_routes: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True, slots=True)
class SecurityPolicy:
    secret_prefix: str = "secret://"


@dataclass(frozen=True, slots=True)
class PolicySet:
    retry: RetryPolicy = RetryPolicy()
    timeout: TimeoutPolicy = TimeoutPolicy()
    concurrency: ConcurrencyPolicy = ConcurrencyPolicy()
    rate_limit: RateLimitPolicy = RateLimitPolicy()
    execution: ExecutionPolicy = ExecutionPolicy()
    security: SecurityPolicy = SecurityPolicy()
