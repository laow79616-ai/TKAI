"""Errors for optional local telemetry infrastructure."""


class TelemetryError(RuntimeError):
    """Base telemetry error."""


class ExporterNotFoundError(TelemetryError):
    """Raised for a missing named exporter."""
