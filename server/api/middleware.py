"""Small ASGI middleware with no logging or global request context."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from uuid import uuid4

from server.production.runtime import ProductionRuntime

from .errors import map_error

AsgiMessage = dict[str, object]
AsgiScope = dict[str, object]
AsgiReceive = Callable[[], Awaitable[AsgiMessage]]
AsgiSend = Callable[[AsgiMessage], Awaitable[None]]
AsgiApp = Callable[[AsgiScope, AsgiReceive, AsgiSend], Awaitable[None]]


class RequestIdMiddleware:
    """Attach one opaque request id to a request scope and its HTTP response."""

    def __init__(self, app: AsgiApp) -> None:
        self._app = app

    async def __call__(
        self, scope: AsgiScope, receive: AsgiReceive, send: AsgiSend
    ) -> None:
        if scope.get("type") != "http":
            await self._app(scope, receive, send)
            return
        request_id = _request_id(scope) or uuid4().hex
        scope["tkai.request_id"] = request_id

        async def send_with_request_id(message: AsgiMessage) -> None:
            if message.get("type") == "http.response.start":
                source_headers = message.get("headers", ())
                headers = (
                    list(source_headers)
                    if isinstance(source_headers, (list, tuple))
                    else []
                )
                headers.append((b"x-request-id", request_id.encode("ascii")))
                message = {**message, "headers": headers}
            await send(message)

        await self._app(scope, receive, send_with_request_id)


def _request_id(scope: AsgiScope) -> str | None:
    """Read a supplied request id without retaining request state."""
    headers = scope.get("headers", ())
    if not isinstance(headers, (list, tuple)):
        return None
    for entry in headers:
        if not isinstance(entry, tuple) or len(entry) != 2:
            continue
        key, value = entry
        if key == b"x-request-id" and isinstance(value, bytes):
            return value.decode("ascii", errors="ignore") or None
    return None


class ExceptionMiddleware:
    """Convert known Foundation errors to JSON without logging or global state."""

    def __init__(self, app: AsgiApp) -> None:
        self._app = app

    async def __call__(
        self, scope: AsgiScope, receive: AsgiReceive, send: AsgiSend
    ) -> None:
        try:
            await self._app(scope, receive, send)
        except Exception as error:
            mapped = map_error(error)
            if mapped.status_code == 500:
                raise
            payload = json.dumps(mapped.error.to_dict()).encode("utf-8")
            await send(
                {
                    "type": "http.response.start",
                    "status": mapped.status_code,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(payload)).encode("ascii")),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": payload})


class SecurityHeadersMiddleware:
    """Append a small, deterministic set of browser hardening headers."""

    _headers = (
        (b"x-content-type-options", b"nosniff"),
        (b"x-frame-options", b"DENY"),
        (b"referrer-policy", b"strict-origin-when-cross-origin"),
        (
            b"content-security-policy",
            b"default-src 'self'; frame-ancestors 'none'; base-uri 'self'",
        ),
    )

    def __init__(self, app: AsgiApp, runtime: ProductionRuntime) -> None:
        self._app = app
        self._runtime = runtime

    async def __call__(
        self, scope: AsgiScope, receive: AsgiReceive, send: AsgiSend
    ) -> None:
        async def send_with_security_headers(message: AsgiMessage) -> None:
            if (
                self._runtime.configuration.security_headers_enabled
                and message.get("type") == "http.response.start"
            ):
                source_headers = message.get("headers", ())
                headers = (
                    list(source_headers)
                    if isinstance(source_headers, (list, tuple))
                    else []
                )
                headers.extend(self._headers)
                message = {**message, "headers": headers}
            await send(message)

        await self._app(scope, receive, send_with_security_headers)


class RateLimitMiddleware:
    """Apply an injected single-process limiter without storing request bodies."""

    def __init__(self, app: AsgiApp, runtime: ProductionRuntime) -> None:
        self._app = app
        self._runtime = runtime

    async def __call__(
        self, scope: AsgiScope, receive: AsgiReceive, send: AsgiSend
    ) -> None:
        if scope.get("type") != "http":
            await self._app(scope, receive, send)
            return
        decision = self._runtime.rate_limiter.allow(_client_key(scope))
        if decision.allowed:
            await self._app(scope, receive, send)
            return
        self._runtime.metrics.increment("http.rate_limited")
        payload = b'{"error":{"code":"rate_limited","message":"Rate limit exceeded."}}'
        await send(
            {
                "type": "http.response.start",
                "status": 429,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(payload)).encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": payload})


class ObservabilityMiddleware:
    """Emit sanitized request outcome entries and count local request metrics."""

    def __init__(self, app: AsgiApp, runtime: ProductionRuntime) -> None:
        self._app = app
        self._runtime = runtime

    async def __call__(
        self, scope: AsgiScope, receive: AsgiReceive, send: AsgiSend
    ) -> None:
        if scope.get("type") != "http":
            await self._app(scope, receive, send)
            return
        status = 500

        async def capture_status(message: AsgiMessage) -> None:
            nonlocal status
            if message.get("type") == "http.response.start":
                candidate = message.get("status")
                if isinstance(candidate, int):
                    status = candidate
            await send(message)

        try:
            await self._app(scope, receive, capture_status)
        finally:
            self._runtime.metrics.increment("http.requests")
            self._runtime.metrics.increment(f"http.status.{status}")
            self._runtime.logger.log(
                "INFO",
                "http.request",
                request_id=_request_id(scope),
                method=scope.get("method", ""),
                path=scope.get("path", ""),
                status=status,
            )


def _client_key(scope: AsgiScope) -> str:
    """Derive a local limiter key from ASGI client information only."""
    client = scope.get("client")
    if isinstance(client, tuple) and client and isinstance(client[0], str):
        return client[0]
    return "unknown"
