import pytest

from command_center import (
    CommandCenterAPI,
    CommandCenterPlatform,
    CommandCenterScope,
)


class FakeApp:
    def __init__(self) -> None:
        self.routes: list[tuple[str, object, tuple[str, ...]]] = []

    def add_api_route(
        self,
        path: str,
        endpoint: object,
        *,
        methods: list[str],
        tags: list[str],
    ) -> None:
        self.routes.append((path, endpoint, tuple(methods)))


def test_api_contract_and_registration() -> None:
    platform = CommandCenterPlatform()
    api = CommandCenterAPI(platform)
    scope = CommandCenterScope("tenant", "workspace", "actor")
    assert len(api.ROUTES) == 10
    assert "/command-center/control-planes" in api.ROUTES
    assert api.get("/command-center/operations", scope)["jobs"]["running"] == 0
    app = FakeApp()
    from command_center import register_command_center_routes

    register_command_center_routes(app, platform)
    assert [route[0] for route in app.routes] == list(api.ROUTES)
    with pytest.raises(KeyError):
        api.get("/command-center/unknown", scope)
