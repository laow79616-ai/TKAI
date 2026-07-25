"""Policy-driven provider failover independent of routing and transports."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar

from .errors import (
    AuthenticationError,
    CapabilityNotSupportedError,
    FallbackExhaustedError,
    ModelNotFoundError,
    ProviderConfigurationError,
    ProviderResponseError,
    ProviderTimeoutError,
    RateLimitError,
)

T = TypeVar("T")
R = TypeVar("R")


class FailureKind(str, Enum):
    """Safe failure categories used to decide retry and failover behavior."""

    TEMPORARY = "temporary"
    PERMANENT = "permanent"


@dataclass(frozen=True, slots=True)
class FallbackCandidate(Generic[T]):
    """One ordered candidate supplied by a capability-routing caller."""

    name: str
    value: T

    def __post_init__(self) -> None:
        """Reject unnamed candidates so diagnostics remain useful and safe."""
        if not self.name:
            raise ValueError("Fallback candidate name cannot be empty")


def default_failure_classifier(error: BaseException) -> FailureKind:
    """Classify only known transient provider failures as safe to retry."""
    if isinstance(
        error,
        (ConnectionError, TimeoutError, ProviderTimeoutError, RateLimitError),
    ):
        return FailureKind.TEMPORARY
    if isinstance(error, ProviderResponseError):
        return FailureKind.TEMPORARY
    if isinstance(
        error,
        (
            AuthenticationError,
            CapabilityNotSupportedError,
            ModelNotFoundError,
            ProviderConfigurationError,
        ),
    ):
        return FailureKind.PERMANENT
    return FailureKind.PERMANENT


@dataclass(frozen=True, slots=True)
class FallbackPolicy:
    """Retry, candidate budget, and blacklist rules for provider failover.

    ``retry_budget`` is the number of retries allowed for each temporarily
    failing candidate. ``max_attempts`` caps all operations across the ordered
    candidate list, including retries. Candidates listed in
    ``blocked_providers`` are never invoked.
    """

    max_attempts: int = 3
    retry_budget: int = 0
    blocked_providers: frozenset[str] = field(default_factory=frozenset)
    classifier: Callable[[BaseException], FailureKind] = default_failure_classifier

    def __post_init__(self) -> None:
        """Validate bounded retry configuration when a policy is created."""
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least one")
        if self.retry_budget < 0:
            raise ValueError("retry_budget cannot be negative")

    def classify(self, error: BaseException) -> FailureKind:
        """Return the policy's retry classification for an operation failure."""
        return self.classifier(error)


class FallbackEngine:
    """Execute an ordered capability-router candidate list under one policy.

    This class intentionally has no knowledge of ``ProviderManager`` or a
    provider API. Callers retain routing ownership and pass their stable,
    capability-filtered candidates to :meth:`execute` or :meth:`stream`.
    """

    def __init__(self, policy: FallbackPolicy | None = None) -> None:
        self.policy = policy or FallbackPolicy()
        self._runtime_blacklist: set[str] = set()

    def blacklist(self, provider_name: str) -> None:
        """Prevent a provider from receiving later operations in this engine."""
        if not provider_name:
            raise ValueError("Provider name cannot be empty")
        self._runtime_blacklist.add(provider_name)

    def unblacklist(self, provider_name: str) -> None:
        """Allow a previously runtime-blacklisted provider to be considered."""
        self._runtime_blacklist.discard(provider_name)

    def is_blacklisted(self, provider_name: str) -> bool:
        """Return whether policy or runtime state excludes a provider."""
        return (
            provider_name in self.policy.blocked_providers
            or provider_name in self._runtime_blacklist
        )

    def ordered_candidates(
        self, candidates: Sequence[FallbackCandidate[T]]
    ) -> tuple[FallbackCandidate[T], ...]:
        """Filter blacklisted candidates while preserving caller-supplied order."""
        seen: set[str] = set()
        ordered: list[FallbackCandidate[T]] = []
        for candidate in candidates:
            if candidate.name in seen:
                raise ValueError(f"Duplicate fallback candidate: {candidate.name}")
            seen.add(candidate.name)
            if not self.is_blacklisted(candidate.name):
                ordered.append(candidate)
        return tuple(ordered)

    def execute(
        self,
        candidates: Sequence[FallbackCandidate[T]],
        operation: Callable[[T], R],
    ) -> R:
        """Return the first successful operation result within the policy budget."""
        ordered = self.ordered_candidates(candidates)
        attempts, summaries = self._attempt_state()
        retries: dict[str, int] = {}
        index = 0
        while index < len(ordered) and len(attempts) < self.policy.max_attempts:
            candidate = ordered[index]
            try:
                attempts.append(candidate.name)
                return operation(candidate.value)
            except Exception as error:
                summaries.append(self._summary(candidate, error))
                retry_count = retries.get(candidate.name, 0)
                if (
                    self.policy.classify(error) is FailureKind.TEMPORARY
                    and retry_count < self.policy.retry_budget
                    and len(attempts) < self.policy.max_attempts
                ):
                    retries[candidate.name] = retry_count + 1
                    continue
                index += 1
        raise FallbackExhaustedError(tuple(attempts), tuple(summaries))

    def stream(
        self,
        candidates: Sequence[FallbackCandidate[T]],
        operation: Callable[[T], Iterator[R]],
    ) -> Iterator[R]:
        """Yield a stream, falling over only before the first business item.

        A switch after output could duplicate or reorder user-visible content,
        so any post-output exception is propagated without invoking another
        candidate.
        """
        ordered = self.ordered_candidates(candidates)
        attempts, summaries = self._attempt_state()
        retries: dict[str, int] = {}
        index = 0
        while index < len(ordered) and len(attempts) < self.policy.max_attempts:
            candidate = ordered[index]
            emitted = False
            try:
                attempts.append(candidate.name)
                for item in operation(candidate.value):
                    emitted = True
                    yield item
                return
            except Exception as error:
                if emitted:
                    raise
                summaries.append(self._summary(candidate, error))
                retry_count = retries.get(candidate.name, 0)
                if (
                    self.policy.classify(error) is FailureKind.TEMPORARY
                    and retry_count < self.policy.retry_budget
                    and len(attempts) < self.policy.max_attempts
                ):
                    retries[candidate.name] = retry_count + 1
                    continue
                index += 1
        raise FallbackExhaustedError(tuple(attempts), tuple(summaries))

    @staticmethod
    def _attempt_state() -> tuple[list[str], list[str]]:
        """Create fresh per-invocation attempt and safe-summary collections."""
        return [], []

    @staticmethod
    def _summary(candidate: FallbackCandidate[T], error: BaseException) -> str:
        """Describe an attempt without exposing raw provider error text or secrets."""
        return f"{candidate.name}: {type(error).__name__}"
