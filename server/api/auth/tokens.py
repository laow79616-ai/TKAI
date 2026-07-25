"""Opaque, local-only token helpers for the reference authentication service."""

from __future__ import annotations

from secrets import token_urlsafe

from .models import AuthenticationError


def create_bearer_token() -> str:
    """Create a high-entropy opaque token without encoding user credentials."""
    return token_urlsafe(32)


def parse_bearer_token(authorization: str | None) -> str:
    """Extract a token from one strict Bearer authorization value."""
    if authorization is None:
        raise AuthenticationError("Bearer token is required.")
    scheme, separator, token = authorization.partition(" ")
    if scheme != "Bearer" or not separator or not token.strip():
        raise AuthenticationError("Authorization must use the Bearer scheme.")
    return token.strip()
