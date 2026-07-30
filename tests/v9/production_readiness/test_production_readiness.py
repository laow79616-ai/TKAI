"""Regression contracts for TKAI V9 production readiness."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from server.api.app import create_app

ROOT = Path(__file__).resolve().parents[3]


def load_verifier():
    path = ROOT / "scripts" / "verify-v9-production.py"
    spec = importlib.util.spec_from_file_location("verify_v9_production", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exactly_ten_completed_v9_components() -> None:
    verifier = load_verifier()
    report = verifier.audit()
    assert report["status"] == "ready", report["errors"]
    assert report["framework_count"] == 10
    assert all(item["status"] == "completed" for item in report["frameworks"])


def test_aggregate_openapi_is_unique_and_v9_is_get_only() -> None:
    schema = create_app().openapi()
    operations = [
        (method, path, operation)
        for path, methods in schema["paths"].items()
        for method, operation in methods.items()
        if method in {"get", "post", "put", "patch", "delete"}
    ]
    ids = [operation.get("operationId") for _, _, operation in operations]
    assert len([item for item in ids if item]) == len(set(item for item in ids if item))
    assert all(
        method == "get" for method, path, _ in operations if path.startswith("/v9/")
    )
    assert any(path.startswith("/v9/planning/") for _, path, _ in operations)


def test_release_inventory_excludes_sensitive_and_generated_content() -> None:
    verifier = load_verifier()
    files = verifier.inventory()
    assert files
    for path in files:
        assert ".git" not in path.parts
        assert "artifacts" not in path.parts
        assert "node_modules" not in path.parts
        assert path.name != ".env"
        assert path.suffix not in {".cookie", ".cookies", ".session"}
