"""Offline tests for the V10 Sovereign Compatibility Mesh."""

from pathlib import Path

import pytest

from tkai.v10.compatibility_mesh import (
    SUPPORTED_VERSIONS,
    CompatibilityProfile,
    CompatibilityRule,
    CompatibilityStatus,
    RuleType,
    SovereignCompatibilityMesh,
    SubjectType,
)
from tkai.v10.compatibility_mesh.api import (
    GET_ROUTES,
    openapi_contract,
    register_routes,
)


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def add_api_route(
        self, path: str, handler: object, *, methods: list[str], **_: object
    ) -> None:
        self.routes[path] = (methods[0], handler)


def test_structure_versions_profile_and_safety() -> None:
    root = Path(__file__).resolve().parents[3]
    required = set(
        """
        profiles registry versions subjects contracts interfaces schemas capabilities
        frameworks modules services extensions configuration storage runtime apis
        openapi dashboard ai_studio deployment integrity trust governance rules
        negotiation assessments gaps conflicts plans validation diagnostics health
        metrics audit security events contracts_api interfaces_api lifecycle
        dashboard_projection api
        """.split()
    )
    package = root / "src/tkai/v10/compatibility_mesh"
    assert required <= {item.name for item in package.iterdir() if item.is_dir()}
    mesh = SovereignCompatibilityMesh()
    assert {item["version"] for item in mesh.discover("versions")} == set(
        SUPPORTED_VERSIONS
    )
    mesh.register(
        "profiles",
        CompatibilityProfile("p", "framework:v6", SubjectType.FRAMEWORK, "v6"),
    )
    assert (
        mesh.overview()["execution"] == "disabled"
        and mesh.diagnostics()["runtime_mutation"] is False
    )
    assert not any(
        hasattr(mesh, name)
        for name in (
            "execute",
            "apply",
            "migrate",
            "upgrade",
            "rollback",
            "deploy",
            "approve",
        )
    )


def test_rules_and_negotiation_are_deterministic_and_bounded() -> None:
    mesh = SovereignCompatibilityMesh()
    exact = CompatibilityRule("exact", RuleType.EXACT_VERSION_MATCH, "v10", "v10")
    changed = CompatibilityRule("type", RuleType.TYPE_CHANGE)
    assert mesh.evaluate_rule(exact) is CompatibilityStatus.COMPATIBLE
    first = mesh.negotiate("n", "v6:x", "v10:x", "v6", "v10", (exact, changed))
    second = SovereignCompatibilityMesh().negotiate(
        "n", "v6:x", "v10:x", "v6", "v10", (exact, changed)
    )
    assert (
        first == second and first.result_status is CompatibilityStatus.REVIEW_REQUIRED
    )
    with pytest.raises(ValueError, match="bounded"):
        mesh.negotiate("large", "s", "t", "v6", "v10", (exact,) * 101)


def test_security_metrics_api_and_openapi() -> None:
    mesh = SovereignCompatibilityMesh()
    with pytest.raises(ValueError, match="secret-bearing"):
        mesh.register(
            "profiles",
            CompatibilityProfile(
                "bad", "s", SubjectType.MODULE, "v9", safe_metadata={"api_key": "x"}
            ),
        )
    assert mesh.serialize({"password": "x"}) == {"password": "[REDACTED]"}
    app = FakeApp()
    register_routes(app)
    assert len(GET_ROUTES) == 34 and {method for method, _ in app.routes.values()} == {
        "GET"
    }
    assert all(set(ops) == {"get"} for ops in openapi_contract()["paths"].values())
    assert (
        "register_v10_sovereign_compatibility_mesh_routes(app)"
        in (Path(__file__).resolve().parents[3] / "server/api/app.py").read_text()
    )
