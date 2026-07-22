"""Injectable HTTP-status mapping transport primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .errors import (
    AuthenticationError,
    ModelNotFoundError,
    ProviderResponseError,
    ProviderTimeoutError,
    RateLimitError,
)


@dataclass(frozen=True, slots=True)
class HTTPResponse:
    status_code: int
    json: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)


def raise_for_status(
    response: HTTPResponse, *, provider: str, model: str | None = None
) -> None:
    """Map HTTP failures to secret-safe provider exceptions."""
    status = response.status_code
    request_id = response.headers.get("x-request-id", "")
    message = f"Provider '{provider}' request failed ({status})"
    if request_id:
        message += f" request_id={request_id}"
    if status in (401, 403):
        raise AuthenticationError(message)
    if status == 404 and model:
        raise ModelNotFoundError(message)
    if status == 408:
        raise ProviderTimeoutError(message)
    if status == 429:
        raise RateLimitError(message)
    if status >= 400:
        raise ProviderResponseError(message)
