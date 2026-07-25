"""Explicit adaptive runtime scheduler with no ProviderManager takeover."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import timedelta
from enum import Enum
from threading import RLock

from tkai.circuit_breaker import CircuitBreaker, CircuitState, ThresholdStrategy
from tkai.health import HealthStatus
from tkai.telemetry import TelemetryManager


class SchedulingPolicy(str, Enum):
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_LATENCY = "least_latency"
    LEAST_ERROR = "least_error"
    LOWEST_COST = "lowest_cost"
    HIGHEST_SCORE = "highest_score"
    STICKY_SESSION = "sticky_session"
    ADAPTIVE = "adaptive"


@dataclass(frozen=True, slots=True)
class ProviderScore:
    provider: str
    health_score: float
    latency_score: float
    success_rate: float
    error_rate: float
    cost_weight: float
    static_priority: int
    total_score: float
    breaker_state: CircuitState


@dataclass(frozen=True, slots=True)
class SchedulingDecision:
    provider: str | None
    policy: SchedulingPolicy
    candidates: tuple[str, ...]
    scores: tuple[ProviderScore, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class _ProviderState:
    provider: str
    latency_ms: float = 0.0
    successes: int = 0
    failures: int = 0
    cost: float = 0.0
    priority: int = 0
    weight: int = 1
    health: HealthStatus = HealthStatus.HEALTHY


class RuntimeScheduler:
    """Select registered provider names using explicit policies and statistics."""

    def __init__(
        self,
        *,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
        telemetry: TelemetryManager | None = None,
    ) -> None:
        if recovery_timeout_seconds < 0:
            raise ValueError("recovery_timeout_seconds must not be negative.")
        self._states: dict[str, _ProviderState] = {}
        self._breakers: dict[str, CircuitBreaker] = {}
        self._sticky: dict[str, str] = {}
        self._cursor = 0
        self._lock = RLock()
        self._strategy = ThresholdStrategy(
            failure_threshold=failure_threshold,
            open_duration=timedelta(seconds=recovery_timeout_seconds),
        )
        self.telemetry = telemetry

    def register(
        self,
        provider: str,
        *,
        latency_ms: float = 0.0,
        cost: float = 0.0,
        priority: int = 0,
        weight: int = 1,
        health: HealthStatus = HealthStatus.HEALTHY,
    ) -> None:
        """Register immutable static provider data; actual invocation stays external."""
        if not provider or latency_ms < 0 or cost < 0 or weight < 1:
            raise ValueError("Invalid scheduler provider configuration.")
        with self._lock:
            self._states[provider] = _ProviderState(
                provider, latency_ms, 0, 0, cost, priority, weight, health
            )
            self._breakers[provider] = CircuitBreaker(provider, strategy=self._strategy)

    def record_result(
        self, provider: str, *, success: bool, latency_ms: float | None = None
    ) -> None:
        """Record an externally observed result and update the reused breaker."""
        with self._lock:
            state = self._states[provider]
            updated = replace(
                state,
                successes=state.successes + int(success),
                failures=state.failures + int(not success),
                latency_ms=state.latency_ms if latency_ms is None else latency_ms,
            )
            self._states[provider] = updated
            breaker = self._breakers[provider]
            if success:
                breaker.record_success()
            else:
                breaker.record_failure()

    def schedule(
        self,
        policy: SchedulingPolicy = SchedulingPolicy.ADAPTIVE,
        *,
        session_id: str | None = None,
    ) -> SchedulingDecision:
        """Return a stable decision without invoking a provider or network endpoint."""
        with self._lock:
            eligible = [
                state
                for state in self._states.values()
                if state.health is not HealthStatus.UNHEALTHY
                and self._breakers[state.provider].allow_request()
            ]
            eligible.sort(key=lambda state: state.provider)
            scores = tuple(self._score(state) for state in eligible)
            provider = self._select(policy, eligible, scores, session_id)
            decision = SchedulingDecision(
                provider,
                policy,
                tuple(item.provider for item in eligible),
                scores,
                (
                    "No eligible provider"
                    if provider is None
                    else "Selected by explicit policy"
                ),
            )
        if self.telemetry is not None:
            self.telemetry.platform.counter(
                "runtime.scheduler.decisions", policy=policy.value
            )
        return decision

    def _select(
        self,
        policy: SchedulingPolicy,
        states: list[_ProviderState],
        scores: tuple[ProviderScore, ...],
        session_id: str | None,
    ) -> str | None:
        if not states:
            return None
        if policy is SchedulingPolicy.STICKY_SESSION and session_id:
            selected = self._sticky.get(session_id)
            if selected in {state.provider for state in states}:
                return selected
        if policy is SchedulingPolicy.ROUND_ROBIN:
            selected = states[self._cursor % len(states)].provider
            self._cursor += 1
        elif policy is SchedulingPolicy.WEIGHTED_ROUND_ROBIN:
            expanded = [state for state in states for _ in range(state.weight)]
            selected = expanded[self._cursor % len(expanded)].provider
            self._cursor += 1
        elif policy is SchedulingPolicy.LEAST_LATENCY:
            selected = min(
                states, key=lambda item: (item.latency_ms, item.provider)
            ).provider
        elif policy is SchedulingPolicy.LEAST_ERROR:
            selected = min(
                states, key=lambda item: (self._error_rate(item), item.provider)
            ).provider
        elif policy is SchedulingPolicy.LOWEST_COST:
            selected = min(states, key=lambda item: (item.cost, item.provider)).provider
        else:
            selected = max(
                scores, key=lambda item: (item.total_score, item.provider)
            ).provider
        if policy is SchedulingPolicy.STICKY_SESSION and session_id:
            self._sticky[session_id] = selected
        return selected

    def _score(self, state: _ProviderState) -> ProviderScore:
        total = state.successes + state.failures
        success_rate = state.successes / total if total else 1.0
        error_rate = state.failures / total if total else 0.0
        health_score = 1.0 if state.health is HealthStatus.HEALTHY else 0.5
        latency_score = 1.0 / (1.0 + state.latency_ms)
        cost_weight = 1.0 / (1.0 + state.cost)
        priority_score = float(state.priority) / 100.0
        total_score = (
            health_score
            + latency_score
            + success_rate
            - error_rate
            + cost_weight
            + priority_score
        )
        return ProviderScore(
            state.provider,
            health_score,
            latency_score,
            success_rate,
            error_rate,
            cost_weight,
            state.priority,
            total_score,
            self._breakers[state.provider].snapshot.state,
        )

    @staticmethod
    def _error_rate(state: _ProviderState) -> float:
        total = state.successes + state.failures
        return state.failures / total if total else 0.0
