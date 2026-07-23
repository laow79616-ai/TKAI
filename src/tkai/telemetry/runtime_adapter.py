"""Explicit runtime-adjacent telemetry adapter without Runtime API changes."""

from .manager import TelemetryManager


class TelemetryRuntimeAdapter:
    def __init__(self, manager: TelemetryManager) -> None:
        self.manager = manager

    def start(self) -> None:
        self.manager.start()

    def stop(self) -> None:
        self.manager.stop()

    def health(self) -> dict[str, object]:
        return self.manager.summary()
