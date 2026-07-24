"""Stable errors for the local-only Marketplace Server Statistics Foundation."""


class StatisticsError(Exception):
    """Base Statistics Foundation error without transport or storage detail."""


class StatisticsValidationError(StatisticsError):
    """Raised when an explicit Statistics model has invalid structure or value."""


class StatisticsConflictError(StatisticsError):
    """Raised for duplicate source or record identifiers."""


class StatisticsNotFoundError(StatisticsError):
    """Raised when a requested explicit Statistics object is absent."""


class StatisticsSourceNotFoundError(StatisticsNotFoundError):
    """Raised when a requested Statistics source is absent."""


class StatisticsRecordNotFoundError(StatisticsNotFoundError):
    """Raised when a requested Statistics record is absent."""


class StatisticsStateError(StatisticsError):
    """Raised when a Statistics source lifecycle operation is not allowed."""


class StatisticsAggregationError(StatisticsError):
    """Raised when requested records cannot be aggregated under one clear rule."""


class StatisticsClosedError(StatisticsError):
    """Raised after a closed Statistics service accepts a write operation."""
