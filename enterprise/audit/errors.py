"""Stable Audit Foundation errors with no storage, transport, or secret detail."""

from ..errors import EnterpriseArchitectureError


class AuditError(EnterpriseArchitectureError):
    """Base error for Audit Foundation operations."""


class AuditValidationError(AuditError):
    """Raised when a descriptor is structurally invalid."""


class AuditNotFoundError(AuditError):
    """Raised when an explicit event or service is unavailable."""


class AuditConflictError(AuditError):
    """Raised for duplicate event or registry identifiers."""


class AuditClosedError(AuditError):
    """Raised when an operation requires an open reference service."""


class AuditRedactionError(AuditError):
    """Raised for an invalid redaction policy or bounded traversal error."""


class AuditQueryError(AuditError):
    """Raised for invalid declarative audit queries."""


class AuditIntegrityError(AuditError):
    """Raised when a deterministic reference integrity chain is invalid."""


class AuditCapacityError(AuditError):
    """Raised when a configured reference service capacity rejects an event."""
