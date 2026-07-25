"""Local metric registry and aggregation without remote export ownership."""

from __future__ import annotations

from threading import RLock

from .models import Metric, MetricKind


class MetricsRegistry:
    def __init__(self) -> None:
        self._metrics: list[Metric] = []
        self._lock = RLock()

    def register(self, metric: Metric) -> None:
        self.record(metric)

    def record(self, metric: Metric) -> None:
        with self._lock:
            self._metrics.append(metric)

    def counter(self, name: str, value: float = 1.0, **labels: str) -> Metric:
        metric = Metric(name, value, labels=labels, kind=MetricKind.COUNTER)
        self.record(metric)
        return metric

    def gauge(self, name: str, value: float, **labels: str) -> Metric:
        metric = Metric(name, value, labels=labels, kind=MetricKind.GAUGE)
        self.record(metric)
        return metric

    def histogram(self, name: str, value: float, **labels: str) -> Metric:
        metric = Metric(name, value, labels=labels, kind=MetricKind.HISTOGRAM)
        self.record(metric)
        return metric

    def snapshot(self) -> list[Metric]:
        with self._lock:
            return list(self._metrics)

    def clear(self) -> None:
        with self._lock:
            self._metrics.clear()
