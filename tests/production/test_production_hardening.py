"""Offline tests for explicit Marketplace Server production hardening."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from server.api.middleware import SecurityHeadersMiddleware
from server.production.config import (
    ProductionConfigurationError,
    ProductionConfigurationLoader,
)
from server.production.logging import StructuredLogger
from server.production.metrics import InMemoryMetrics
from server.production.rate_limit import InMemoryRateLimiter
from server.production.runtime import ProductionRuntime


def test_configuration_loads_only_known_dotenv_values_and_environment_overrides(
    tmp_path: Path,
) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "TKAI_LOG_LEVEL=warning\nTKAI_RATE_LIMIT_REQUESTS=3\n"
        "TKAI_RATE_LIMIT_WINDOW_SECONDS=2\nTKAI_SECURITY_HEADERS_ENABLED=false\n",
        encoding="utf-8",
    )

    configuration = ProductionConfigurationLoader.load(
        dotenv_path=dotenv, environment={"TKAI_LOG_LEVEL": "debug", "UNUSED": "x"}
    )

    assert configuration.log_level == "DEBUG"
    assert configuration.rate_limit_requests == 3
    assert configuration.rate_limit_window_seconds == 2
    assert configuration.security_headers_enabled is False

    dotenv.write_text("UNKNOWN=value\n", encoding="utf-8")
    with pytest.raises(ProductionConfigurationError, match="known TKAI"):
        ProductionConfigurationLoader.load(dotenv_path=dotenv)


def test_structured_logging_redacts_credentials_and_metrics_snapshot_is_stable() -> (
    None
):
    messages: list[str] = []
    logger = StructuredLogger(sink=messages.append)
    logger.log("INFO", "request", password="hidden", token="hidden", answer=42)

    payload = json.loads(messages[0])
    assert payload["fields"] == {
        "answer": 42,
        "password": "[REDACTED]",
        "token": "[REDACTED]",
    }

    metrics = InMemoryMetrics()
    metrics.increment("requests")
    metrics.increment("requests")
    assert metrics.snapshot().to_dict() == {"requests": 2}


def test_rate_limiter_is_local_deterministic_and_replaceable() -> None:
    limiter = InMemoryRateLimiter(2, 60)

    assert limiter.allow("client").allowed is True
    assert limiter.allow("client").remaining == 0
    assert limiter.allow("client").allowed is False
    assert limiter.allow("other").allowed is True


def test_runtime_shutdown_is_idempotent_and_health_is_caller_driven() -> None:
    closed: list[str] = []
    runtime = ProductionRuntime(closers=(lambda: closed.append("storage"),))

    assert runtime.health.snapshot().to_dict() == {
        "started": False,
        "ready": False,
        "live": True,
    }
    runtime.start()
    assert runtime.health.snapshot().to_dict()["ready"] is True
    runtime.close()
    runtime.close()

    assert closed == ["storage"]
    assert runtime.health.snapshot().to_dict() == {
        "started": True,
        "ready": False,
        "live": False,
    }


def test_security_headers_are_appended_without_logging_request_data() -> None:
    messages: list[dict[str, object]] = []

    async def app(_scope: dict[str, object], _receive: object, send: object) -> None:
        await send({"type": "http.response.start", "status": 200, "headers": []})

    async def receive() -> dict[str, object]:
        return {"type": "http.request"}

    async def send(message: dict[str, object]) -> None:
        messages.append(message)

    middleware = SecurityHeadersMiddleware(app, ProductionRuntime())
    asyncio.run(middleware({"type": "http"}, receive, send))

    headers = dict(messages[0]["headers"])
    assert headers[b"x-content-type-options"] == b"nosniff"
    assert headers[b"x-frame-options"] == b"DENY"
    assert headers[b"referrer-policy"] == b"strict-origin-when-cross-origin"
    assert b"content-security-policy" in headers
