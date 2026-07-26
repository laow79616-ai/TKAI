from pathlib import Path

from security_platform import SecurityPlatform
from security_platform.api import register_security_routes
from security_platform.dashboard import SECTIONS


class App:
    def __init__(self) -> None:
        self.routes: set[tuple[str, str]] = set()

    def add_api_route(
        self, path: str, endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        self.routes.update((method, path) for method in methods)


def test_api_dashboard_and_frontend_contract() -> None:
    app = App()
    register_security_routes(app, SecurityPlatform())
    for path in (
        "/security/identity",
        "/security/auth",
        "/security/policy",
        "/security/secrets",
        "/security/incidents",
        "/security/compliance",
    ):
        assert any(route_path == path for _, route_path in app.routes)
    assert SECTIONS == (
        "identity",
        "authentication",
        "authorization",
        "secrets",
        "threats",
        "incidents",
        "compliance",
        "audit",
    )
    root = Path(__file__).resolve().parents[2]
    app_source = (root / "dashboard/frontend/src/App.tsx").read_text(encoding="utf-8")
    api_source = (root / "dashboard/frontend/src/api.ts").read_text(encoding="utf-8")
    for section in SECTIONS:
        assert f"security-{section}" in app_source
    assert "/security/${resource}" in api_source
