"""Small ASGI middleware with no logging or global request context."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from uuid import uuid4

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
