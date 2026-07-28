"""Dependency-free Prometheus-style Device Center metrics."""

METRIC_NAMES = (
    "tiktok_devices_total",
    "tiktok_devices_ready",
    "tiktok_devices_running",
    "tiktok_devices_offline",
    "tiktok_device_health_score",
    "tiktok_device_recoveries",
    "tiktok_device_failures",
    "tiktok_device_cpu_usage",
    "tiktok_device_memory_usage",
)


class DeviceCenterMetrics:
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
