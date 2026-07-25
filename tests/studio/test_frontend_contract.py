"""Static offline checks for the independent frontend foundation files."""

from __future__ import annotations

from pathlib import Path


def test_frontend_declares_vite_react_routes_and_frozen_api_endpoints() -> None:
    root = Path(__file__).resolve().parents[2] / "studio" / "frontend"
    package = (root / "package.json").read_text(encoding="utf-8")
    api = (root / "src" / "api.ts").read_text(encoding="utf-8")
    pages = (root / "src" / "pages.ts").read_text(encoding="utf-8")

    assert "vite" in package and "react" in package and "typecheck" in package
    for endpoint in (
        "/projects",
        "/workflows",
        "/executions",
        "/health",
        "/system",
        "/version",
    ):
        assert endpoint in api
    for page in ("dashboard", "projects", "workflow", "execution", "logs"):
        assert page in pages
