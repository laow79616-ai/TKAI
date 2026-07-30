"""Offline tests for the V10 Sovereign Integrity Mesh."""

from pathlib import Path

import pytest

from tkai.v10.contracts import Scope
from tkai.v10.integrity_mesh import (
    CompatibilityIntegrity,
    DependencyIntegrity,
    DependencyIssueType,
    EvidenceType,
    IntegrityEvidence,
    IntegrityProfile,
    IntegrityRelationship,
    IntegritySubject,
    RelationshipType,
    ReleaseIntegrity,
    SovereignIntegrityMesh,
    SubjectType,
    VerificationReference,
    VerificationStatus,
)
from tkai.v10.integrity_mesh.api import GET_ROUTES, openapi_contract, register_routes
from tkai.v10.integrity_mesh.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v10.integrity_mesh.security import authorize_metadata_read


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def add_api_route(
        self, path: str, handler: object, *, methods: list[str], **_: object
    ) -> None:
        self.routes[path] = (methods[0], handler)


def test_structure_profile_and_subjects() -> None:
    root = Path(__file__).resolve().parents[3]
    required = set(
        "profiles registry subjects evidence verification hashes relationships "
        "dependencies compatibility configuration storage artifacts releases "
        "diagnostics health metrics audit security events contracts interfaces "
        "lifecycle dashboard api".split()
    )
    package = root / "src/tkai/v10/integrity_mesh"
    assert required <= {item.name for item in package.iterdir() if item.is_dir()}
    profile = IntegrityProfile("p", "subject", SubjectType.FRAMEWORK)
    subject = IntegritySubject("s", SubjectType.API, "v10:api")
    assert profile.version == "10.0.0" and subject.reference == "v10:api"
    assert len(SubjectType) == 15


def test_evidence_verification_and_relationships_are_advisory() -> None:
    mesh = SovereignIntegrityMesh()
    mesh.register("evidence", IntegrityEvidence("e", EvidenceType.HASH, "s", "local:e"))
    for status in VerificationStatus:
        item = VerificationReference(f"v-{status.value}", "s", status)
        mesh.register("verification", item)
        assert item.automatic_repair is False
    for kind in RelationshipType:
        item = IntegrityRelationship(f"r-{kind.value}", "s", "t", kind)
        mesh.register("relationships", item)
        assert item.reference_only is True
    assert len(mesh.discover("verification")) == 5


def test_dependencies_compatibility_and_releases_are_reference_only() -> None:
    mesh = SovereignIntegrityMesh()
    for issue in DependencyIssueType:
        mesh.register("dependencies", DependencyIntegrity(issue.value, "s", "d", issue))
    release = ReleaseIntegrity("release", "s", checksum_reference="sha256:abc")
    mesh.register("releases", release)
    assert release.signing_service is False
    assert len(mesh.discover("dependencies")) == 7
    compatibility = mesh.discover("compatibility")
    assert len(compatibility) == 5
    assert all(
        isinstance(item, CompatibilityIntegrity)
        and not item.migration
        and not item.upgrade
        and not item.rollback
        for item in compatibility
    )


def test_health_metrics_dashboard_observability_and_security() -> None:
    mesh = SovereignIntegrityMesh()
    mesh.register(
        "profiles",
        IntegrityProfile("p", "s", SubjectType.MODULE, safe_metadata={"label": "ok"}),
    )
    assert mesh.health()["status"] == "healthy"
    assert mesh.metrics()["v10_integrity_mesh_profiles_total"] == 1
    assert mesh.audit() and mesh.traces() and mesh.structured_logs()
    assert mesh.diagnostics()["runtime_mutation"] is False
    snapshot = dashboard_snapshot(mesh)
    assert len(DASHBOARD_SECTIONS) == 11
    assert snapshot["read_only"] is True and snapshot["actions"] == ()
    scope = Scope("tenant", "workspace")
    authorize_metadata_read(scope, scope, role_references=("reader",))
    with pytest.raises(ValueError, match="secret-bearing"):
        mesh.register(
            "profiles",
            IntegrityProfile(
                "bad", "s", SubjectType.MODULE, safe_metadata={"token": "x"}
            ),
        )
    assert mesh.serialize({"password": "x"}) == {"password": "[REDACTED]"}


def test_api_and_openapi_are_get_only_and_integrated() -> None:
    app = FakeApp()
    register_routes(app)
    assert len(GET_ROUTES) == 10
    assert {method for method, _ in app.routes.values()} == {"GET"}
    assert all(
        set(operations) == {"get"}
        for operations in openapi_contract()["paths"].values()
    )
    source = (Path(__file__).resolve().parents[3] / "server/api/app.py").read_text()
    assert "register_v10_sovereign_integrity_mesh_routes(app)" in source


def test_no_action_or_mutation_capabilities() -> None:
    mesh = SovereignIntegrityMesh()
    assert mesh.overview()["execution"] == "disabled"
    forbidden = (
        "execute",
        "apply",
        "repair",
        "rewrite",
        "mutate",
        "sign",
        "publish",
        "deploy",
        "upgrade",
        "migrate",
        "rollback",
        "browser",
        "tiktok",
    )
    assert not any(hasattr(mesh, name) for name in forbidden)
