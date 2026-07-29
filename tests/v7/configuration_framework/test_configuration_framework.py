from datetime import UTC, datetime, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient

from tkai.v7.configuration_framework import (
    ConfigurationDefinition,
    ConfigurationFramework,
    Environment,
    EnvironmentProfile,
    FieldDefinition,
    Lifecycle,
    OverrideArtifact,
    PrecedenceRule,
    SchemaDefinition,
    Scope,
    SourceDefinition,
    SourceKind,
)
from tkai.v7.configuration_framework.api import (
    CONFIGURATION_ENDPOINTS,
    register_configuration_framework_routes,
)


def build_framework() -> tuple[ConfigurationFramework, Scope]:
    framework = ConfigurationFramework()
    scope = Scope("tenant-a", "workspace-a", "app")
    rule = PrecedenceRule(
        "rule-1",
        "development",
        "1.0.0",
        (SourceKind.BUILTIN_DEFAULTS, SourceKind.ENVIRONMENT_VARIABLE),
        "environment references override built-in references",
    )
    framework.register_profile(
        EnvironmentProfile(
            "development",
            Environment.DEVELOPMENT,
            frozenset(rule.ordered_sources),
            rule,
        )
    )
    framework.register_schema(
        SchemaDefinition(
            "schema-1",
            "app",
            "1.0.0",
            (
                FieldDefinition("workers", "integer", required=True, minimum=1),
                FieldDefinition("api_key", "string", secret=True),
            ),
        )
    )
    framework.register_source(
        SourceDefinition(
            "defaults",
            SourceKind.BUILTIN_DEFAULTS,
            "1.0.0",
            scope,
            Environment.DEVELOPMENT,
            "development",
            {"workers": 1, "api_key": "secret://app/key"},
        )
    )
    framework.register_source(
        SourceDefinition(
            "environment",
            SourceKind.ENVIRONMENT_VARIABLE,
            "1.0.0",
            scope,
            Environment.DEVELOPMENT,
            "development",
            {"workers": 2},
        )
    )
    framework.register_configuration(
        ConfigurationDefinition(
            "config-1",
            "Application",
            "local configuration",
            "app",
            "platform",
            "1.0.0",
            Environment.DEVELOPMENT,
            "development",
            scope,
            ("environment", "defaults"),
            "schema-1",
            lifecycle=Lifecycle.ACTIVE_REFERENCE,
            tags=frozenset({"compatible-v6"}),
        )
    )
    return framework, scope


def test_deterministic_resolution_validation_and_secret_references() -> None:
    framework, scope = build_framework()
    effective = framework.resolve("config-1", scope)
    assert effective.effective_field_references["workers"] == 2
    assert effective.effective_field_references["api_key"] == "secret://app/key"
    assert effective.source_provenance["workers"] == "environment"
    assert effective.validation_summary["status"] == "valid"
    assert effective.security_summary["read_only"] is True


def test_snapshot_integrity_diff_redaction_and_advisory_plan() -> None:
    framework, scope = build_framework()
    effective = framework.resolve("config-1", scope)
    snapshot = framework.snapshot(effective, "audit-1")
    assert framework.verify_snapshot(snapshot.snapshot_id, effective)
    diff = framework.compare(
        "before",
        {"api_key": "secret://old"},
        "after",
        {"api_key": "literal-must-not-leak"},
    )
    assert diff.entries[0].after_reference == "[REDACTED]"
    plan = framework.plan_change(
        "before",
        "after",
        diff.diff_id,
        "validation-1",
        "compat-1",
        "security-1",
        "rollback-1",
        "audit-2",
    )
    assert plan.advisory_only is True
    assert not hasattr(framework, "apply")


def test_expired_override_diagnostic_and_scope_isolation() -> None:
    framework, scope = build_framework()
    framework.registry.register_override(
        OverrideArtifact(
            "override-1",
            scope,
            SourceKind.TEST_OVERRIDE,
            "app",
            {"workers": 3},
            "test",
            "owner",
            datetime.now(UTC) - timedelta(seconds=1),
        )
    )
    assert framework.diagnose(scope)[0]["code"] == "expired-override"


def test_get_only_routes_and_no_mutation_or_secret_endpoint() -> None:
    app = FastAPI()
    framework, _ = build_framework()
    register_configuration_framework_routes(app, framework)
    client = TestClient(app)
    for endpoint in CONFIGURATION_ENDPOINTS:
        url = f"/v7/configuration/{endpoint}"
        params = {"tenant": "tenant-a", "workspace": "workspace-a", "namespace": "app"}
        assert client.get(url, params=params).status_code == 200
        assert client.post(url, params=params).status_code == 405
    paths = app.openapi()["paths"]
    assert all(
        set(paths[f"/v7/configuration/{item}"]) == {"get"}
        for item in CONFIGURATION_ENDPOINTS
    )
    assert not any("apply" in path or "secret-value" in path for path in paths)


def test_v6_import_remains_available() -> None:
    import tkai

    assert tkai is not None
