"""Transport-neutral authentication dependency helpers."""

from __future__ import annotations

from .models import AuthenticatedUser
from .service import ReferenceAuthenticationService
from .tokens import parse_bearer_token


class AuthenticationDependency:
    """Verify one supplied Bearer header through an explicitly injected service."""

    def __init__(self, service: ReferenceAuthenticationService) -> None:
        self._service = service

    def __call__(self, authorization: str | None) -> AuthenticatedUser:
        """Return the authenticated administrator or raise a stable auth error."""
        return self._service.verify_token(parse_bearer_token(authorization)).user
