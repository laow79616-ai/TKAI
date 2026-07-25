"""Offline coverage for the single-administrator authentication foundation."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from server.api import ApiDependencies, create_app
from server.api.auth import (
    AdministratorCredentials,
    AuthenticationConfiguration,
    AuthenticationDependency,
    AuthenticationError,
    LoginRequest,
    ReferenceAuthenticationService,
)
from server.api.errors import map_error


class FakeFastAPI:
    """Offline route recorder that exposes no HTTP or socket behavior."""

    def __init__(self, **_metadata: object) -> None:
        self.state = SimpleNamespace()
        self.routes: dict[str, object] = {}

    def add_api_route(self, path: str, endpoint: object, **_metadata: object) -> None:
        self.routes[path] = endpoint

    def add_middleware(self, _middleware: object, **_kwargs: object) -> None:
        pass

    def add_exception_handler(self, _error: object, _handler: object) -> None:
        pass


def fake_factory(**kwargs: object) -> FakeFastAPI:
    """Create a local route recorder without importing FastAPI."""
    return FakeFastAPI(**kwargs)


def _service() -> ReferenceAuthenticationService:
    return ReferenceAuthenticationService(
        AuthenticationConfiguration(
            administrator=AdministratorCredentials(username="admin", password="secret")
        ),
        clock=lambda: datetime(2026, 7, 25, tzinfo=timezone.utc),
        token_factory=lambda: "reference-token",
    )


def test_login_success_and_token_verification_are_explicit_and_local() -> None:
    """A configured single administrator can receive and verify an opaque token."""
    service = _service()

    response = service.login(LoginRequest(username="admin", password="secret"))
    info = service.verify_token(response.access_token)

    assert response.token_type == "Bearer"
    assert info.user.username == "admin"
    assert info.access_token == "reference-token"


def test_login_failure_and_unconfigured_service_do_not_disclose_credentials() -> None:
    """Invalid credentials and absent configuration use stable authentication errors."""
    with pytest.raises(AuthenticationError, match="Invalid administrator credentials"):
        _service().login(LoginRequest(username="admin", password="incorrect"))
    with pytest.raises(AuthenticationError, match="not configured"):
        ReferenceAuthenticationService().login(
            LoginRequest(username="admin", password="x")
        )


def test_revoked_and_invalid_tokens_are_rejected_by_service_and_dependency() -> None:
    """Revocation is in-memory and the dependency enforces strict Bearer syntax."""
    service = _service()
    token = service.login(
        LoginRequest(username="admin", password="secret")
    ).access_token
    dependency = AuthenticationDependency(service)

    assert dependency(f"Bearer {token}").administrator is True
    service.revoke_token(token)
    with pytest.raises(AuthenticationError, match="revoked"):
        service.verify_token(token)
    with pytest.raises(AuthenticationError, match="Bearer scheme"):
        dependency("Token invalid")


def test_authentication_endpoints_use_the_injected_service_and_no_global_state() -> (
    None
):
    """Login, me, and logout use the app-specific explicit service instance."""
    service = _service()
    dependencies = replace(ApiDependencies.create(), authentication_service=service)
    app = create_app(dependencies=dependencies, app_factory=fake_factory)

    login = app.routes["/auth/login"](LoginRequest(username="admin", password="secret"))
    assert app.routes["/auth/me"](f"Bearer {login.access_token}").username == "admin"
    assert app.routes["/auth/logout"](f"Bearer {login.access_token}") == {
        "revoked": True
    }
    with pytest.raises(AuthenticationError):
        app.routes["/auth/me"](f"Bearer {login.access_token}")


def test_authentication_errors_map_to_unauthorized_http_contract() -> None:
    """Authentication failures map to 401 without Foundation changes."""
    mapped = map_error(AuthenticationError("Bearer token is invalid."))

    assert mapped.status_code == 401
    assert mapped.error.code == "authentication_error"
