"""Immutable, single-administrator authentication contracts."""

from __future__ import annotations

from datetime import datetime
from hashlib import pbkdf2_hmac
from secrets import token_hex

from pydantic import BaseModel, ConfigDict, Field


class AuthenticationError(Exception):
    """Raised for invalid credentials, malformed tokens, and revoked tokens."""


class AdministratorCredentials(BaseModel):
    """Explicit administrator credentials; callers must supply them securely."""

    model_config = ConfigDict(frozen=True)

    username: str = Field(min_length=1, max_length=256)
    password: str = Field(min_length=1, max_length=1024, repr=False)

    def model_post_init(self, _context: object) -> None:
        """Replace submitted plaintext with a salted PBKDF2 verifier immediately."""
        if self.password.startswith("pbkdf2_sha256$"):
            return
        salt = token_hex(16)
        digest = pbkdf2_hmac(
            "sha256", self.password.encode(), bytes.fromhex(salt), 310_000
        ).hex()
        object.__setattr__(self, "password", f"pbkdf2_sha256$310000${salt}${digest}")


class AuthenticationConfiguration(BaseModel):
    """Single-administrator configuration with no environment or database lookup."""

    model_config = ConfigDict(frozen=True)

    administrator: AdministratorCredentials | None = None
    token_ttl_seconds: int = Field(default=3600, gt=0, le=86_400)


class LoginRequest(BaseModel):
    """Validated credentials submitted to the reference login endpoint."""

    model_config = ConfigDict(frozen=True)

    username: str = Field(min_length=1, max_length=256)
    password: str = Field(min_length=1, max_length=1024, repr=False)


class AuthenticatedUser(BaseModel):
    """The sole authenticated administrator identity; it does not carry roles."""

    model_config = ConfigDict(frozen=True)

    username: str
    administrator: bool = True


class TokenInfo(BaseModel):
    """Opaque in-memory Bearer token state with an explicit expiry instant."""

    model_config = ConfigDict(frozen=True)

    access_token: str = Field(min_length=1, repr=False)
    token_type: str = "Bearer"
    user: AuthenticatedUser
    issued_at: datetime
    expires_at: datetime
    revoked: bool = False


class LoginResponse(BaseModel):
    """Bearer token response returned after a successful single-admin login."""

    model_config = ConfigDict(frozen=True)

    access_token: str = Field(min_length=1)
    token_type: str = "Bearer"
    expires_at: datetime
    user: AuthenticatedUser
