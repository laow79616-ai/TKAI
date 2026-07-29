"""Local alert metadata without notification transport."""

from ..contracts import Alert, Severity

EXTERNAL_NOTIFICATIONS_ENABLED = False

__all__ = ("Alert", "EXTERNAL_NOTIFICATIONS_ENABLED", "Severity")
