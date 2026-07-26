"""Offline source-contract checks for the Marketplace Server Dashboard MVP."""

from __future__ import annotations

from pathlib import Path


def _frontend() -> Path:
    return Path(__file__).resolve().parents[2] / "dashboard" / "frontend"


def test_dashboard_declares_react_vite_typescript_and_tailwind_sources() -> None:
    """The independent dashboard retains a reproducible client-side toolchain."""
    root = _frontend()
    package = (root / "package.json").read_text(encoding="utf-8")

    for dependency in ("react", "vite", "typescript", "tailwindcss"):
        assert dependency in package
    assert (root / "vite.config.ts").is_file()
    assert (root / "tailwind.config.ts").is_file()


def test_dashboard_api_client_uses_only_existing_server_api_contracts() -> None:
    """Dashboard requests use API endpoints and attach the opaque Bearer header."""
    client = (_frontend() / "src" / "api.ts").read_text(encoding="utf-8")

    for endpoint in (
        "/auth/login",
        "/auth/me",
        "/auth/logout",
        "/registry",
        "/publishers",
        "/packages",
        "/versions",
        "/search",
        "/statistics",
        "/health",
        "/version",
    ):
        assert endpoint in client
    assert "authorization" in client and "Bearer ${this.token}" in client


def test_dashboard_declares_mvp_pages_components_and_authentication_flow() -> None:
    """All MVP pages are routed and login state remains in the UI boundary."""
    root = _frontend() / "src"
    app = (root / "App.tsx").read_text(encoding="utf-8")
    pages = (root / "pages.tsx").read_text(encoding="utf-8")
    auth = (root / "auth.tsx").read_text(encoding="utf-8")
    components = (root / "components.tsx").read_text(encoding="utf-8")

    for page in (
        "LoginPage",
        "DashboardHome",
        "RegistryPage",
        "PublishersPage",
        "PackagesPage",
        "VersionsPage",
        "SearchPage",
        "StatisticsPage",
        "HealthPage",
        "NotFoundPage",
    ):
        assert page in pages or page in app
    for component in (
        "Sidebar",
        "Header",
        "Card",
        "Table",
        "SearchBar",
        "Loading",
        "ErrorBoundary",
    ):
        assert component in components
    assert "sessionStorage" in auth and "login" in auth and "logout" in auth


def test_dashboard_exposes_enterprise_app_store_sections() -> None:
    root = _frontend() / "src"
    app = (root / "App.tsx").read_text(encoding="utf-8")
    pages = (root / "pages.tsx").read_text(encoding="utf-8")
    client = (root / "api.ts").read_text(encoding="utf-8")
    for section in (
        "Store Home",
        "Categories",
        "Application Details",
        "Installed Applications",
        "App Store Updates",
        "App Store Licenses",
        "Subscriptions",
        "App Store Publishers",
        "App Store Reviews",
        "Moderation",
        "App Store Analytics",
    ):
        assert section in app
    assert "AppStorePage" in pages
    assert '"/app-store"' in client
