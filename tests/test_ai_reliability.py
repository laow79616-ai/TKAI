"""Offline reliability coverage."""

from __future__ import annotations

import pytest

from tkai.ai import (
    HTTPResponse,
    ModelNotFoundError,
    ProviderConfigurationError,
    RateLimitError,
    load_provider_config,
    raise_for_status,
)
from tkai.ai.retry import retry_call


def test_config_expands_environment_and_rejects_missing(monkeypatch) -> None:
    monkeypatch.setenv("TKAI_KEY", "secret")
    default, configs = load_provider_config(
        {
            "providers": {
                "default": "openai",
                "openai": {"type": "openai", "api_key": "${TKAI_KEY}"},
            }
        }
    )
    assert default == "openai" and configs[0].api_key == "secret"
    with pytest.raises(ProviderConfigurationError):
        load_provider_config({"providers": {"openai": {"api_key": "${MISSING}"}}})


def test_http_mapping_and_retry_are_offline() -> None:
    with pytest.raises(ModelNotFoundError):
        raise_for_status(HTTPResponse(404), provider="x", model="m")
    calls = 0

    def operation() -> str:
        nonlocal calls
        calls += 1
        if calls < 2:
            raise RateLimitError("limited")
        return "ok"

    assert retry_call(operation, max_retries=1) == "ok"
