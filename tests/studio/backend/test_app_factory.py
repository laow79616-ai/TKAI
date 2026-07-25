"""Offline Studio application-host smoke tests."""

from __future__ import annotations

from types import SimpleNamespace

from studio.backend import StudioDependencies, create_studio_app


class FakeFastAPI:
    """In-process app recorder with no socket or network side effects."""

    def __init__(self, **metadata: object) -> None:
        self.metadata = metadata
        self.state = SimpleNamespace()
        self.routes: list[tuple[str, tuple[str, ...], object]] = []

    def add_api_route(self, path: str, endpoint: object, *, methods: list[str]) -> None:
        self.routes.append((path, tuple(methods), endpoint))


def fake_factory(**kwargs: object) -> FakeFastAPI:
    """Create the test-only fake host application."""
    return FakeFastAPI(**kwargs)


def test_app_factory_registers_rest_routes_with_explicit_dependencies() -> None:
    """App creation is side-effect free and accepts an explicit dependency container."""
    dependencies = StudioDependencies.create()
    app = create_studio_app(dependencies=dependencies, app_factory=fake_factory)

    assert isinstance(app, FakeFastAPI)
    assert app.state.studio_dependencies is dependencies
    assert len(app.routes) == 16
    assert app.metadata["title"] == "TKAI Studio"
