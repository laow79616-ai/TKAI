"""Complete V11 platform invariants."""

from tkai.v11.platform import COMPONENTS, V11Platform
from tkai.v11.platform_api import GET_ROUTES, openapi_contract, route_handlers


def test_all_requested_components_are_registered() -> None:
    assert len(COMPONENTS) == 22
    names = {item.name for item in COMPONENTS}
    assert {
        "Autonomous Intelligence Core",
        "Autonomous Knowledge Graph",
        "Autonomous Reasoning Fabric",
        "Autonomous Decision Fabric",
        "Autonomous Planning Fabric",
        "Autonomous Operations Fabric",
        "Autonomous Recovery Fabric",
        "Autonomous Trust Fabric",
        "Autonomous Integrity Fabric",
        "Autonomous Compatibility Fabric",
        "Autonomous Governance Fabric",
        "Autonomous Validation Fabric",
        "Context Engine",
        "Registry Engine",
        "Relationship Engine",
        "Dependency Engine",
        "Contract Engine",
        "Interface Engine",
        "Diagnostics Engine",
        "Metrics Engine",
        "Audit Engine",
        "Security Engine",
    } == names


def test_every_component_is_advisory_deterministic_and_non_executable() -> None:
    platform = V11Platform()
    for component in COMPONENTS:
        projection = platform.component(component.slug)
        assert projection["architecture"] == {
            "local_first": True,
            "metadata_driven": True,
            "deterministic": True,
            "advisory": True,
            "read_only": True,
        }
        assert not any(projection["execution"].values())


def test_complete_api_is_get_only_and_deterministic() -> None:
    platform = V11Platform()
    handlers = route_handlers(platform)
    assert tuple(handlers) == GET_ROUTES
    assert len(GET_ROUTES) == 133
    schema = openapi_contract()
    assert all(set(operations) == {"get"} for operations in schema["paths"].values())
    assert platform.overview() == platform.overview()
