"""Offline mock-only tests for the V10 Sovereign Reasoning Mesh."""
# ruff: noqa: E501

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from tkai.v10.contracts import Scope
from tkai.v10.reasoning_mesh import (
    SUPPORTED_GENERATIONS,
    Alternative,
    Assessment,
    Claim,
    ClaimType,
    Confidence,
    ConstraintReference,
    ConstraintType,
    Contradiction,
    ContradictionType,
    EvidenceReference,
    Explanation,
    Inference,
    InferenceType,
    Premise,
    ReasoningContext,
    ReasoningProfile,
    SovereignReasoningMesh,
    UncertaintyType,
)
from tkai.v10.reasoning_mesh.api import GET_ROUTES, openapi_contract, register_routes
from tkai.v10.reasoning_mesh.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v10.reasoning_mesh.events import EVENT_FABRIC_COMPATIBILITY, EVENT_TYPES
from tkai.v10.reasoning_mesh.security import authorize_metadata_read


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def add_api_route(
        self, path: str, handler: object, *, methods: list[str], **_: object
    ) -> None:
        self.routes[path] = (methods[0], handler)


def test_repository_path_structure_and_compatibility() -> None:
    root = Path(__file__).resolve().parents[3]
    assert root.resolve() == Path(r"C:\Users\laow7\Documents\TKAI").resolve()
    required = set(
        """profiles registry contexts claims premises evidence inferences assumptions constraints
    alternatives confidence uncertainty contradictions explanations assessments compatibility governance
    integrity trust knowledge validation diagnostics health metrics audit security events contracts interfaces
    lifecycle dashboard api""".split()
    )
    package = root / "src/tkai/v10/reasoning_mesh"
    assert required <= {p.name for p in package.iterdir() if p.is_dir()}
    mesh = SovereignReasoningMesh()
    assert {r.generation for r in mesh.discover("compatibility")} == set(
        SUPPORTED_GENERATIONS
    )


def test_immutable_profiles_contexts_claims_and_types() -> None:
    profile = ReasoningProfile("p", "subject", safe_metadata={"label": "safe"})
    context = ReasoningContext("c", "subject", "bounded")
    claim = Claim("claim", "safe summary", "subject", ClaimType.OBSERVATIONAL)
    with pytest.raises(FrozenInstanceError):
        profile.health = "bad"  # type: ignore[misc]
    assert len(ClaimType) == 13 and context.status == "registered"
    mesh = SovereignReasoningMesh()
    for registry, record in (
        ("profiles", profile),
        ("contexts", context),
        ("claims", claim),
    ):
        mesh.register(registry, record)


def test_premise_evidence_inference_are_references_only() -> None:
    mesh = SovereignReasoningMesh()
    premise = Premise("p", "summary", "v10:knowledge")
    evidence = EvidenceReference("e", "v10:knowledge", "subject")
    inference = Inference(
        "i", InferenceType.DEDUCTIVE_REFERENCE, ("p",), ("e",), "claim", "rule"
    )
    mesh.register("premises", premise)
    mesh.register("evidence", evidence)
    mesh.register("inferences", inference)
    assert (
        evidence.reference_only and inference.metadata_only and len(InferenceType) == 10
    )


def test_constraints_alternatives_confidence_uncertainty_and_contradictions() -> None:
    mesh = SovereignReasoningMesh()
    mesh.register(
        "constraints", ConstraintReference("c", ConstraintType.SECURITY, "policy:x")
    )
    mesh.register("alternatives", Alternative("a", "alternative"))
    mesh.register(
        "confidence", Confidence("confidence", None, "unknown", "insufficient")
    )
    contradiction = Contradiction(
        "x", ContradictionType.CLAIM_CONFLICT, "a", "b", "conflict"
    )
    mesh.register("contradictions", contradiction)
    assert (
        len(ConstraintType) == 15
        and len(UncertaintyType) == 8
        and len(ContradictionType) == 10
    )
    assert contradiction.automatic_resolution is False


def test_safe_explanations_assessments_and_hidden_reasoning_protection() -> None:
    mesh = SovereignReasoningMesh()
    explanation = Explanation("e", "Safe user-facing summary")
    assessment = Assessment("a", "security", "subject", "advisory result")
    mesh.register("explanations", explanation)
    mesh.register("assessments", assessment)
    assert explanation.safe_user_facing_only and assessment.advisory_only
    with pytest.raises(ValueError, match="hidden"):
        mesh.register(
            "profiles",
            ReasoningProfile("bad", "s", safe_metadata={"chain_of_thought": "secret"}),
        )
    assert mesh.serialize({"api_key": "secret"}) == {"api_key": "[REDACTED]"}


def test_bounds_security_health_metrics_events_and_dashboard() -> None:
    mesh = SovereignReasoningMesh(per_registry_limit=5)
    mesh.register("profiles", ReasoningProfile("p", "s"))
    assert (
        mesh.health()["readiness"]
        and mesh.metrics()["v10_reasoning_profiles_total"] == 1
    )
    assert len(mesh.metrics()) == 15 and len(EVENT_TYPES) == 16
    assert EVENT_FABRIC_COMPATIBILITY.startswith("v7-")
    assert len(DASHBOARD_SECTIONS) == 26 and dashboard_snapshot(mesh)["actions"] == ()
    with pytest.raises(ValueError, match="between 0 and 100"):
        mesh.discover("profiles", limit=101)
    scope = Scope("tenant", "workspace")
    authorize_metadata_read(scope, scope, role_references=("reader",))
    with pytest.raises(PermissionError):
        authorize_metadata_read(scope, scope)


def test_api_openapi_server_and_forbidden_endpoints() -> None:
    app = FakeApp()
    register_routes(app)
    assert len(GET_ROUTES) == 25 and {method for method, _ in app.routes.values()} == {
        "GET"
    }
    assert all(set(ops) == {"get"} for ops in openapi_contract()["paths"].values())
    forbidden = (
        "execute",
        "apply",
        "migrate",
        "upgrade",
        "rollback",
        "mutate",
        "start",
        "stop",
        "restart",
        "deploy",
        "recover",
        "secret",
        "chain-of-thought",
        "scratchpad",
        "hidden-prompt",
    )
    assert not any(any(word in path for word in forbidden) for path in GET_ROUTES)
    root = Path(__file__).resolve().parents[3]
    assert (
        "register_v10_sovereign_reasoning_mesh_routes(app)"
        in (root / "server/api/app.py").read_text()
    )


def test_no_execution_mutation_scanning_network_or_platform_actions() -> None:
    mesh = SovereignReasoningMesh()
    assert mesh.overview()["execution"] == "disabled"
    assert all(value is False for value in mesh.diagnostics().values())
    assert not any(
        hasattr(mesh, name)
        for name in (
            "execute",
            "apply",
            "plan",
            "approve",
            "scan",
            "search",
            "ingest",
            "mutate",
            "deploy",
            "browser",
            "tiktok",
            "start",
            "stop",
            "restart",
            "rollback",
        )
    )
