"""Workspace Foundation errors for local reference registry operations."""


class WorkspaceError(Exception):
    """Base error for explicit reference workspace operations."""


class WorkspaceConflictError(WorkspaceError):
    """Raised when an identifier is already registered."""


class WorkspaceNotFoundError(WorkspaceError):
    """Raised when a caller explicitly requests an unknown identifier."""
