"""Thread-safe, pure-memory single-administrator authentication reference service."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from threading import RLock

from .models import (
    AuthenticatedUser,
    AuthenticationConfiguration,
    AuthenticationError,
    LoginRequest,
    LoginResponse,
    TokenInfo,
)
from .tokens import create_bearer_token

Clock = Callable[[], datetime]
TokenFactory = Callable[[], str]


class ReferenceAuthenticationService:
    """Issue and revoke opaque tokens without persistence, network, or user lookup."""

    def __init__(
        self,
        configuration: AuthenticationConfiguration | None = None,
        *,
        clock: Clock | None = None,
        token_factory: TokenFactory | None = None,
    ) -> None:
        self._configuration = configuration or AuthenticationConfiguration()
        self._clock = clock or _utc_now
        self._token_factory = token_factory or create_bearer_token
        self._tokens: dict[str, TokenInfo] = {}
        self._lock = RLock()

    def verify_credentials(self, request: LoginRequest) -> AuthenticatedUser:
        """Validate explicit single-admin credentials without retaining request data."""
        administrator = self._configuration.administrator
        if administrator is None:
            raise AuthenticationError(
                "Single administrator credentials are not configured."
            )
        valid_username = compare_digest(request.username, administrator.username)
        valid_password = _verify_password(request.password, administrator.password)
        if not valid_username or not valid_password:
            raise AuthenticationError("Invalid administrator credentials.")
        return AuthenticatedUser(username=administrator.username)

    def issue_token(self, user: AuthenticatedUser) -> LoginResponse:
        """Issue a new opaque Bearer token for the verified administrator only."""
        with self._lock:
            administrator = self._configuration.administrator
            if administrator is None or user.username != administrator.username:
                raise AuthenticationError(
                    "Token subject is not the configured administrator."
                )
            token = self._token_factory()
            if not token or token in self._tokens:
                raise AuthenticationError("Token factory returned an invalid token.")
            issued_at = self._now()
            expires_at = issued_at + timedelta(
                seconds=self._configuration.token_ttl_seconds
            )
            info = TokenInfo(
                access_token=token,
                user=user,
                issued_at=issued_at,
                expires_at=expires_at,
            )
            self._tokens[token] = info
            return LoginResponse(
                access_token=token,
                expires_at=expires_at,
                user=user,
            )

    def login(self, request: LoginRequest) -> LoginResponse:
        """Verify explicit credentials and issue one token as one local operation."""
        return self.issue_token(self.verify_credentials(request))

    def verify_token(self, token: str) -> TokenInfo:
        """Verify an opaque token against local state and its explicit expiration."""
        with self._lock:
            try:
                info = self._tokens[token]
            except KeyError as error:
                raise AuthenticationError("Bearer token is invalid.") from error
            if info.revoked:
                raise AuthenticationError("Bearer token has been revoked.")
            if self._now() >= info.expires_at:
                raise AuthenticationError("Bearer token has expired.")
            return info

    def revoke_token(self, token: str) -> TokenInfo:
        """Revoke one issued token idempotently without deleting historical state."""
        with self._lock:
            info = self.verify_token(token)
            revoked = info.model_copy(update={"revoked": True})
            self._tokens[token] = revoked
            return revoked

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            raise AuthenticationError(
                "Authentication clock must return an aware UTC time."
            )
        return value.astimezone(timezone.utc)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _verify_password(candidate: str, encoded: str) -> bool:
    """Verify a salted PBKDF2-SHA256 credential in constant time."""
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = pbkdf2_hmac(
            "sha256", candidate.encode(), bytes.fromhex(salt), int(iterations)
        ).hex()
    except (ValueError, TypeError):
        return False
    return compare_digest(actual, expected)
