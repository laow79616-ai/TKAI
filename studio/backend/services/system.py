"""Safe system information service that never returns secret configuration values."""

from __future__ import annotations

import tkai
from studio.config import StudioSettings


class SystemService:
    """Expose non-sensitive Studio and TKAI version/capability information."""

    def __init__(self, settings: StudioSettings) -> None:
        self._settings = settings

    def report(self) -> dict[str, object]:
        """Return safe static product data for the initial system endpoint."""
        return {
            "studio": {
                "name": self._settings.app_name,
                "version": self._settings.app_version,
                "environment": self._settings.environment,
            },
            "tkai_version": tkai.__version__,
            "capabilities": (
                "projects",
                "visual_workflows",
                "sdk_gateway",
                "reference_memory_storage",
            ),
        }
