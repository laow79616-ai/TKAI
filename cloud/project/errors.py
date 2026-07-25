"""Stable errors for explicit Project Foundation reference operations."""


class ProjectError(Exception):
    """Base Project Foundation error without network or persistence semantics."""


class ProjectConflictError(ProjectError):
    """Raised when a project or relationship identifier conflicts locally."""


class ProjectNotFoundError(ProjectError):
    """Raised when an explicit project identifier is not registered."""
