"""Offline, mock-only tests for the V10 Sovereign Trust Mesh."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from tkai.v10.contracts import Scope
from tkai.v10.trust_mesh import (
    AttestationMetadata,
    CompatibilityMetadata,
    IdentityRecord,
    IntegrityMetadata,
    PrincipalRecord,
    RelationshipStatus,
    SovereignTrustMesh,
    TrustDomainKind,
    TrustDomainRecord,
    TrustMeshProfile,
    TrustRelationship,
    TrustScore,
)
from tkai.v10.trust_mesh.api import GET_ROUTES, openapi_contract, register_routes
from tkai.v10.trust_mesh.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v10.trust_mesh.security import (
    authorize_metadata_read,
    authorize_trust_domain,
)


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def add_api_route(
        self, path: str, handler: object, *, methods: list[str], **_: object
    ) -> None:
        self.routes[path] = (methods[0], handler)


def test_repository_package_structure_and_profile() -> None:
    root = Path(__file__).resolve().parents[3]
    assert root.resolve() == Path(r"C:\Users\laow7\Documents\TKAI").resolve()
    required = set(
        "profiles registry domains identities principals relationships attestations "
        "integrity scores policies constraints governance compatibility analytics "
        "diagnostics health metrics audit security events contracts interfaces "
        "lifecycle dashboard api".split()
    )
    package = root / "src/tkai/v10/trust_mesh"
    assert required <= {path.name for path in package.iterdir() if path.is_dir()}
    profile = TrustMeshProfile(
        "profile",
        trust_domain_references=("domain",),
        identity_references=("identity",),
        principal_references=("principal",),
        relationship_references=("relationship",),
        integrity_references=("integrity",),
        attestation_references=("attestation",),
        governance_references=("governance",),
        compatibility_references=("compatibility",),
        audit=("audit",),
        metadata={"label": "safe"},
    )
    assert profile.version == "10.0.0" and profile.owner == "TKAI"
    with pytest.raises(FrozenInstanceError):
        profile.owner = "other"  # type: ignore[misc]


def test_domains_identities_principals_and_relationships() -> None:
    mesh = SovereignTrustMesh()
    assert {kind.value for kind in TrustDomainKind} == {
        "local_host", "tenant", "workspace", "namespace", "framework",
        "capability", "service", "module", "extension", "runtime",
    }
    scope = Scope("tenant", "workspace", "namespace")
    mesh.register(
        "domains", TrustDomainRecord("domain", TrustDomainKind.TENANT, "Tenant", scope)
    )
    mesh.register("identities", IdentityRecord("identity", "local", "provider", scope))
    mesh.register(
        "principals", PrincipalRecord("principal", "identity", ("reader",), (), scope)
    )
    for status in RelationshipStatus:
        relationship = TrustRelationship(
            f"relationship-{status.value}", "principal", "domain", status, scope=scope
        )
        mesh.register("relationships", relationship)
        assert relationship.grants_trust is False
    assert len(mesh.discover("relationships", scope=scope)) == 6


def test_integrity_attestations_and_scores_are_metadata_only() -> None:
    mesh = SovereignTrustMesh()
    integrity = IntegrityMetadata(
        "integrity", "subject", expected_hash="abc", evidence_references=("e",)
    )
    attestation = AttestationMetadata(
        "attestation", "subject", "local:issuer", evidence_references=("e",)
    )
    score = TrustScore(
        "score", "subject", 0.7, "Local evidence was observed.", ("e",),
        ("Evidence freshness is not verified.",),
    )
    mesh.register("integrity", integrity)
    mesh.register("attestations", attestation)
    mesh.register("scores", score)
    assert integrity.remote_verification is False
    assert attestation.external_attestation is False
    assert score.automatic_decision is False
    with pytest.raises(ValueError, match="between 0 and 1"):
        mesh.register("scores", TrustScore("bad", "subject", 1.1, "invalid"))
    assert not hasattr(mesh, "grant_trust")
    assert not hasattr(mesh, "verify_remotely")


def test_v6_to_v10_federation_and_compatibility_are_reference_only() -> None:
    mesh = SovereignTrustMesh()
    federation = mesh.federation()
    assert federation["generations"] == ("v6", "v7", "v8", "v9", "v10")
    assert federation["reference_only"] is True
    assert federation["automatic_trust"] is False
    records = mesh.discover("compatibility")
    assert len(records) == 5
    assert all(
        isinstance(item, CompatibilityMetadata)
        and item.automatic_migration is False
        for item in records
    )


def test_security_isolation_rbac_and_secret_filtering() -> None:
    scope = Scope("tenant", "workspace", "namespace")
    authorize_metadata_read(scope, scope, role_references=("reader",))
    with pytest.raises(PermissionError, match="RBAC"):
        authorize_metadata_read(scope, scope)
    with pytest.raises(PermissionError, match="tenant isolation"):
        authorize_metadata_read(
            scope, Scope("other", "workspace", "namespace"),
            role_references=("reader",),
        )
    authorize_trust_domain("domain", "domain")
    with pytest.raises(PermissionError, match="trust isolation"):
        authorize_trust_domain("domain", "other")
    mesh = SovereignTrustMesh()
    with pytest.raises(ValueError, match="secret-bearing"):
        mesh.register("profiles", TrustMeshProfile("unsafe", metadata={"token": "x"}))
    assert mesh.serialize({"api_key": "x"}) == {"api_key": "[REDACTED]"}


def test_health_metrics_diagnostics_observability_dashboard_and_audit() -> None:
    mesh = SovereignTrustMesh()
    assert mesh.health()["status"] == "healthy"
    assert mesh.metrics()["v10_trust_mesh_profiles_total"] == 1
    assert mesh.diagnostics()["runtime_mutation"] is False
    assert mesh.audit() and mesh.traces() and mesh.structured_logs()
    dashboard = dashboard_snapshot(mesh)
    assert len(DASHBOARD_SECTIONS) == 11
    assert dashboard["read_only"] is True and dashboard["actions"] == ()


def test_api_openapi_and_server_integration_are_get_only() -> None:
    app = FakeApp()
    register_routes(app)
    assert set(app.routes) == set(GET_ROUTES)
    assert {method for method, _ in app.routes.values()} == {"GET"}
    assert len(GET_ROUTES) == 10
    assert all(
        set(operations) == {"get"}
        for operations in openapi_contract()["paths"].values()
    )
    source = (
        Path(__file__).resolve().parents[3] / "server/api/app.py"
    ).read_text(encoding="utf-8")
    assert "register_v10_sovereign_trust_mesh_routes(app)" in source


def test_local_advisory_surface_has_no_action_capabilities() -> None:
    mesh = SovereignTrustMesh()
    overview = mesh.overview()
    assert overview["execution"] == "disabled"
    assert overview["runtime_mutation"] is False
    assert overview["automatic_trust"] is False
    assert overview["external_network_calls"] is False
    forbidden = (
        "execute", "apply", "mutate", "grant_trust", "attest_externally",
        "verify_remotely", "network_client", "browser", "publish",
    )
    assert not any(hasattr(mesh, name) for name in forbidden)
