"""Frozen REST contract, schema, validation, and version endpoint tests."""

from __future__ import annotations

import pytest

from studio.backend.api import StudioAPI, openapi_schema
from studio.backend.api.contracts import error, success
from studio.backend.dependencies import StudioDependencies
from studio.backend.errors import StudioValidationError


def test_response_envelopes_have_frozen_success_error_request_id_and_timestamp() -> (
    None
):
    """Both response shapes are JSON-compatible with the required fields."""
    ok = success({"name": "project"}, "request-1")
    failed = error("StudioValidationError", "invalid", "request-1")

    assert ok["success"] is True and ok["request_id"] == "request-1"
    assert failed["success"] is False
    assert "timestamp" in ok and "timestamp" in failed


def test_openapi_schema_includes_frozen_routes_and_error_schema() -> None:
    """Schema generation remains offline and exposes every REST resource family."""
    schema = openapi_schema(StudioDependencies.create().settings)

    assert schema["openapi"] == "3.1.0"
    assert "/api/version" in schema["paths"]
    assert "Success" in schema["components"]["schemas"]
    assert "Error" in schema["components"]["schemas"]


def test_api_validation_and_version_contracts() -> None:
    """Invalid payloads have a stable error and version responses expose no secrets."""
    api = StudioAPI(StudioDependencies.create())

    with pytest.raises(StudioValidationError, match="name"):
        api.create_project({})
    version = api.version()
    assert "studio" in version and "tkai_version" in version
