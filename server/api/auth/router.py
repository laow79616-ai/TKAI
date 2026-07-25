"""Authentication route registration with an optional FastAPI dependency adapter."""

from __future__ import annotations

from collections.abc import Callable
from types import ModuleType
from typing import Any

from .dependencies import AuthenticationDependency
from .models import AuthenticatedUser, LoginRequest, LoginResponse
from .service import ReferenceAuthenticationService
from .tokens import parse_bearer_token


def register_routes(
    app: Any,
    service: ReferenceAuthenticationService,
    *,
    fastapi_module: ModuleType | None = None,
) -> None:
    """Register login, identity, and logout routes without global auth state."""
    app.add_api_route(
        "/auth/login",
        login_endpoint(service),
        methods=["POST"],
        tags=["authentication"],
        response_model=LoginResponse,
    )
    app.add_api_route(
        "/auth/me",
        me_endpoint(service, fastapi_module=fastapi_module),
        methods=["GET"],
        tags=["authentication"],
        response_model=AuthenticatedUser,
    )
    app.add_api_route(
        "/auth/logout",
        logout_endpoint(service, fastapi_module=fastapi_module),
        methods=["POST"],
        tags=["authentication"],
    )


def login_endpoint(
    service: ReferenceAuthenticationService,
) -> Callable[[LoginRequest], LoginResponse]:
    """Return a handler that authenticates exactly one submitted administrator."""

    def login(request: LoginRequest) -> LoginResponse:
        return service.login(request)

    return login


def me_endpoint(
    service: ReferenceAuthenticationService,
    *,
    fastapi_module: ModuleType | None = None,
) -> Callable[..., AuthenticatedUser]:
    """Return an identity handler using FastAPI Header injection when available."""
    dependency = AuthenticationDependency(service)
    if fastapi_module is None:

        def me_from_parameter(authorization: str | None = None) -> AuthenticatedUser:
            return dependency(authorization)

        return me_from_parameter
    header = fastapi_module.Header

    def me_from_header(
        authorization: str | None = header(default=None),
    ) -> AuthenticatedUser:
        return dependency(authorization)

    return me_from_header


def logout_endpoint(
    service: ReferenceAuthenticationService,
    *,
    fastapi_module: ModuleType | None = None,
) -> Callable[..., dict[str, bool]]:
    """Return a logout handler that revokes the supplied Bearer token."""
    if fastapi_module is None:

        def logout_from_parameter(authorization: str | None = None) -> dict[str, bool]:
            service.revoke_token(parse_bearer_token(authorization))
            return {"revoked": True}

        return logout_from_parameter
    header = fastapi_module.Header

    def logout_from_header(
        authorization: str | None = header(default=None),
    ) -> dict[str, bool]:
        service.revoke_token(parse_bearer_token(authorization))
        return {"revoked": True}

    return logout_from_header
