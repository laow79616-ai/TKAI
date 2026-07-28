"""Prometheus-compatible Proxy Center metrics."""

from collections import defaultdict

METRICS = (
    "tiktok_proxies_total",
    "tiktok_proxy_active_total",
    "tiktok_proxy_health_score",
    "tiktok_proxy_failures_total",
    "tiktok_proxy_rotations_total",
    "tiktok_proxy_pool_depth",
    "tiktok_proxy_latency_seconds",
)


class ProxyCenterMetrics:
    def __init__(self) -> None:
        self._values: dict[str, float] = defaultdict(float)

    def increment(self, name: str, value: float = 1) -> None:
        if name not in METRICS or value < 0:
            raise ValueError(f"Invalid metric update: {name}")
        self._values[name] += value

    def set(self, name: str, value: float) -> None:
        if name not in METRICS or value < 0:
            raise ValueError(f"Invalid metric value: {name}")
        self._values[name] = value

    def snapshot(self) -> dict[str, float]:
        return {name: self._values[name] for name in METRICS}

    def render_prometheus(self) -> str:
        return "\n".join(f"{name} {value}" for name, value in self.snapshot().items())
