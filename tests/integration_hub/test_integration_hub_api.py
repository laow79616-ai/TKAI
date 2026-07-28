from integration_hub import HubScope, IntegrationHub, IntegrationHubAPI


def test_api_routes_and_scoped_dashboard() -> None:
    hub = IntegrationHub()
    scope = HubScope("tenant", "workspace", "viewer")
    api = IntegrationHubAPI(hub)
    assert set(IntegrationHubAPI.ROUTES) == {
        "/integration-hub/catalog",
        "/integration-hub/connectors",
        "/integration-hub/instances",
        "/integration-hub/mappings",
        "/integration-hub/flows",
        "/integration-hub/credentials",
        "/integration-hub/health",
        "/integration-hub/schedules",
        "/integration-hub/dead-letter",
        "/integration-hub/analytics",
    }
    assert api.get("/integration-hub/catalog", scope) == []
    assert api.get("/integration-hub/analytics", scope)["runs"] == 0
