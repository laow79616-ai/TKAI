"""Typed errors for the additive, local-only Tool SDK."""

from ..errors import SDKError


class ToolSDKError(SDKError):
    """Base error for Tool SDK contracts and reference implementations."""


class ToolNotFoundError(ToolSDKError):
    """Raised when an explicitly named tool is absent from a registry."""


class ToolValidationError(ToolSDKError):
    """Raised before invalid tool arguments reach a reference implementation."""


class ToolExecutionError(ToolSDKError):
    """Raised when a reference tool cannot complete its explicit operation."""
