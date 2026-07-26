"""Prometheus-compatible memory engine metrics."""

METRICS = (
    "memory_objects_total",
    "memory_reads_total",
    "memory_writes_total",
    "memory_cache_hits_total",
    "memory_cache_misses_total",
    "memory_retrieval_total",
    "memory_expired_total",
)


class MemoryMetrics:
    def __init__(self) -> None:
        self.values: dict[str, float] = {name: 0 for name in METRICS}

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in self.values:
            raise ValueError("Unknown memory metric.")
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        if name not in self.values:
            raise ValueError("Unknown memory metric.")
        self.values[name] = value

    def snapshot(self) -> dict[str, float]:
        return dict(self.values)

    def render_prometheus(self) -> str:
        return "".join(f"{name} {value}\n" for name, value in self.values.items())
