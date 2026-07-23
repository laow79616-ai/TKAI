"""Typed Studio backend errors with stable API-facing categories."""

from __future__ import annotations


class StudioError(RuntimeError):
    """Base error for the independent Studio backend product layer."""


class StudioConfigurationError(StudioError):
    """Raised when explicitly provided Studio configuration is invalid."""


class StudioDependencyError(StudioError):
    """Raised when an application dependency has not been configured."""


class StudioNotFoundError(StudioError):
    """Raised when a requested Studio reference does not exist."""


class StudioConflictError(StudioError):
    """Raised when an immutable resource id already exists."""


class StudioValidationError(StudioError):
    """Raised when a Studio API payload fails deterministic validation."""


class StudioExecutionError(StudioError):
    """Raised with the original SDK execution error preserved as its cause."""


class StudioUnavailableError(StudioError):
    """Raised when a required explicit Studio capability is not ready."""
