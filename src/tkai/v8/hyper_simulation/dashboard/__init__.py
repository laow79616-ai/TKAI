"""Read-only dashboard projections."""

from tkai.v8.hyper_simulation.fabric import HyperSimulationFabric

DASHBOARD_SECTIONS = (
    "Simulation Overview",
    "Profiles",
    "Inputs",
    "Baselines",
    "Models",
    "Scenarios",
    "Simulations",
    "Forecasts",
    "Trends",
    "Capacity",
    "Resources",
    "Schedules",
    "Dependencies",
    "Risks",
    "Uncertainty",
    "Confidence",
    "Assumptions",
    "Constraints",
    "Comparisons",
    "Evaluations",
    "Validation",
    "Recommendations",
    "Reviews",
    "Governance",
    "Compatibility",
    "History",
    "Analytics",
    "Diagnostics",
    "Health",
    "Metrics",
    "Audit",
    "Lifecycle",
)


def dashboard_snapshot(fabric: HyperSimulationFabric) -> dict[str, object]:
    return {
        "title": "V8 Hyper Simulation & Forecasting Fabric",
        "read_only": True,
        "advisory": True,
        "sections": DASHBOARD_SECTIONS,
        "data": fabric.snapshot(),
    }
