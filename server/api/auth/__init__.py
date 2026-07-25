"""Reference-only single-administrator authentication contracts and routes."""

from .dependencies import AuthenticationDependency
from .models import (
    AdministratorCredentials,
    AuthenticatedUser,
    AuthenticationConfiguration,
    AuthenticationError,
    LoginRequest,
    LoginResponse,
    TokenInfo,
)
from .service import ReferenceAuthenticationService

__all__ = (
    "AdministratorCredentials",
    "AuthenticatedUser",
    "AuthenticationConfiguration",
    "AuthenticationDependency",
    "AuthenticationError",
    "LoginRequest",
    "LoginResponse",
    "ReferenceAuthenticationService",
    "TokenInfo",
)
