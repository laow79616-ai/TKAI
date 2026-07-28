"""Prometheus-compatible Publishing Center metrics."""

METRICS = (
    "tiktok_publish_jobs_total",
    "tiktok_publish_queue_total",
    "tiktok_publish_success_total",
    "tiktok_publish_failure_total",
    "tiktok_publish_retry_total",
    "tiktok_publish_latency_seconds",
)


class PublishingMetrics:
    def __init__(self) -> None:
        self.values = {name: 0.0 for name in METRICS}

    def increment(self, name: str, amount: float = 1) -> None:
        self.values[name] += amount

    def observe(self, name: str, value: float) -> None:
        self.values[name] = value

    def snapshot(self) -> dict[str, float]:
        return dict(self.values)

    def render_prometheus(self) -> str:
        return "\n".join(f"{key} {value}" for key, value in self.values.items()) + "\n"
