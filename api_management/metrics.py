"""Prometheus-compatible Enterprise AI API Management metrics."""

from collections import defaultdict
from threading import Lock

METRICS = (
    "managed_apis_total",
    "api_gateway_requests_total",
    "api_gateway_failures_total",
    "api_gateway_latency_seconds",
    "api_rate_limit_rejections_total",
    "api_quota_rejections_total",
    "api_subscriptions_total",
    "api_active_consumers_total",
)


class ApiManagementMetrics:
    def __init__(self) -> None:
        self._values: dict[str, float] = defaultdict(float)
        self._lock = Lock()
        for name in METRICS:
            self._values[name] = 0

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRICS:
            raise KeyError(f"Unknown API management metric: {name}")
        with self._lock:
            self._values[name] += amount

    def set(self, name: str, value: float) -> None:
        if name not in METRICS:
            raise KeyError(f"Unknown API management metric: {name}")
        with self._lock:
            self._values[name] = value

    def snapshot(self) -> dict[str, float]:
        with self._lock:
            return dict(self._values)

    def render_prometheus(self) -> str:
        return "".join(
            f"# TYPE {name} counter\n{name} {value:g}\n"
            for name, value in sorted(self.snapshot().items())
        )


__all__ = ("ApiManagementMetrics", "METRICS")
