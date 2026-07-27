"""Prometheus-compatible TikTok browser runtime metrics."""

from collections import defaultdict

METRICS = (
    "tiktok_browser_instances_total",
    "tiktok_browser_active_total",
    "tiktok_browser_launch_total",
    "tiktok_browser_launch_failures_total",
    "tiktok_browser_crashes_total",
    "tiktok_browser_recoveries_total",
    "tiktok_browser_contexts_total",
    "tiktok_browser_pages_total",
    "tiktok_browser_queue_depth",
    "tiktok_browser_launch_latency_seconds",
    "tiktok_browser_memory_bytes",
)


class BrowserRuntimeMetrics:
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
