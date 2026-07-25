"""Explicit errors for optional Policy Engine management."""


class PolicyError(RuntimeError):
    """Base error for policy registration and lifecycle failures."""


class PolicyNotFoundError(PolicyError):
    """Raised when a named policy is not registered."""


class PolicyRegistrationError(PolicyError):
    """Raised when a duplicate or invalid policy is registered."""
