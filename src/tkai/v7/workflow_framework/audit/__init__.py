"""Workflow audit contracts."""

from ..contracts import HistoryEntry

AuditEvent = HistoryEntry
__all__ = ("AuditEvent", "HistoryEntry")
