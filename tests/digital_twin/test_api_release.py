from pathlib import Path

from digital_twin import DigitalTwinAPI, DigitalTwinPlatform, TwinScope


def test_api_contract() -> None:
    api = DigitalTwinAPI(DigitalTwinPlatform())
    scope = TwinScope("tenant", "workspace", "actor")
    assert set(api.ROUTES) == {
        "/digital-twins",
        "/entities",
        "/relationships",
        "/state",
        "/simulation",
        "/predictions",
        "/optimization",
    }
    assert api.get("/digital-twins", scope) == []


def test_release_structure_and_documentation() -> None:
    root = Path(__file__).parents[2]
    modules = (
        "twins",
        "entities",
        "assets",
        "relationships",
        "topology",
        "simulation",
        "state",
        "synchronization",
        "telemetry",
        "events",
        "scenarios",
        "predictions",
        "optimization",
        "dashboard",
        "api",
    )
    for module in modules:
        assert (root / "digital_twin" / module / "__init__.py").is_file()
    for document in (
        "Architecture",
        "TwinLifecycle",
        "Topology",
        "Synchronization",
        "Simulation",
        "Prediction",
        "Optimization",
        "Security",
    ):
        assert (root / "docs" / "digital_twin" / f"{document}.md").is_file()
    assert "digital_twin*" in (root / "pyproject.toml").read_text("utf-8")
