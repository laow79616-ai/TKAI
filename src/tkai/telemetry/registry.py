"""Thread-safe exporter registry."""

from __future__ import annotations

from threading import RLock

from .errors import ExporterNotFoundError, TelemetryError
from .exporter import TelemetryExporter


class TelemetryRegistry:
    def __init__(self) -> None:
        self._exporters: dict[str, TelemetryExporter] = {}
        self._lock = RLock()

    def register(self, name: str, exporter: TelemetryExporter) -> None:
        with self._lock:
            if name in self._exporters:
                raise TelemetryError(f"Exporter '{name}' already registered")
            self._exporters[name] = exporter

    def remove(self, name: str) -> TelemetryExporter:
        with self._lock:
            try:
                return self._exporters.pop(name)
            except KeyError as error:
                raise ExporterNotFoundError(
                    f"Exporter '{name}' is not registered"
                ) from error

    def get(self, name: str) -> TelemetryExporter:
        with self._lock:
            try:
                return self._exporters[name]
            except KeyError as error:
                raise ExporterNotFoundError(
                    f"Exporter '{name}' is not registered"
                ) from error

    def list(self) -> list[tuple[str, TelemetryExporter]]:
        with self._lock:
            return [(name, self._exporters[name]) for name in sorted(self._exporters)]
