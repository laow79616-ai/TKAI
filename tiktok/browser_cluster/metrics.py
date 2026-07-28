"""Dependency-free Prometheus-style browser cluster metrics."""

METRIC_NAMES = (
    "tiktok_browser_cluster_total",
    "tiktok_browser_cluster_nodes",
    "tiktok_browser_cluster_instances",
    "tiktok_browser_cluster_running",
    "tiktok_browser_cluster_queue",
    "tiktok_browser_cluster_failures",
    "tiktok_browser_cluster_recoveries",
    "tiktok_browser_cluster_cpu_usage",
    "tiktok_browser_cluster_memory_usage",
    "tiktok_browser_cluster_launch_latency_seconds",
)


class BrowserClusterMetrics:
    def __init__(self) -> None:
        self.values = {name: 0.0 for name in METRIC_NAMES}

    def set(self, name: str, value: float | int) -> None:
        if name not in self.values:
            raise KeyError(name)
        self.values[name] = float(value)

    def increment(self, name: str, amount: float = 1.0) -> None:
        self.set(name, self.values[name] + amount)

    def render(self) -> str:
        return "\n".join(f"{name} {value}" for name, value in self.values.items())
