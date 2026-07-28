import hashlib
import hmac

import pytest

from integration_platform import (
    METRICS,
    Connector,
    ConnectorType,
    CredentialReference,
    CredentialType,
    DatabaseConnection,
    Integration,
    IntegrationPlatform,
    IntegrationScope,
    IntegrationStatus,
    StorageConnection,
    Webhook,
)
from integration_platform.dashboard import SECTIONS


@pytest.fixture
def configured() -> tuple[IntegrationPlatform, IntegrationScope]:
    platform = IntegrationPlatform()
    scope = IntegrationScope(
        "tenant-a",
        "workspace-a",
        "builder",
        frozenset(
            {
                "integration:read",
                "integration:write",
                "integration:execute",
                "integration:credentials",
                "integration:webhook",
            }
        ),
    )
    platform.create_integration(
        Integration(
            "salesforce",
            "Salesforce",
            "CRM reference integration",
            "salesforce",
            "crm",
            "platform",
            scope.tenant,
            scope.workspace,
        ),
        scope,
    )
    platform.add_credential(
        CredentialReference(
            "credential-a",
            CredentialType.OAUTH2,
            "vault://integrations/salesforce",
            scope.tenant,
            scope.workspace,
        ),
        scope,
    )
    return platform, scope


def test_lifecycle_isolation_rbac_audit_metrics(
    configured: tuple[IntegrationPlatform, IntegrationScope],
) -> None:
    platform, scope = configured
    foreign = IntegrationScope("tenant-b", "workspace-a", "viewer")
    assert platform.list_integrations(foreign) == []
    platform.set_status("salesforce", IntegrationStatus.CONFIGURED, scope)
    platform.set_status("salesforce", IntegrationStatus.VALIDATED, scope)
    platform.set_status("salesforce", IntegrationStatus.ENABLED, scope)
    with pytest.raises(ValueError, match="Invalid lifecycle"):
        platform.set_status("salesforce", IntegrationStatus.DRAFT, scope)
    assert platform.audit[0].action == "integration.create"
    assert platform.metrics.snapshot()["integrations_total"] == 1


def test_credentials_connectors_mapping_retry_dedup_and_dead_letter(
    configured: tuple[IntegrationPlatform, IntegrationScope],
) -> None:
    platform, scope = configured
    with pytest.raises(ValueError, match="opaque"):
        CredentialReference(
            "bad", CredentialType.API_KEY, "plain-secret", "tenant-a", "workspace-a"
        )
    connector = platform.add_connector(
        Connector(
            "rest-a",
            "salesforce",
            "REST",
            ConnectorType.REST_API,
            scope.tenant,
            scope.workspace,
            "credential-a",
            "https://example.invalid",
            request_mapping={"customer": "Account"},
            response_mapping={"Id": "id"},
            allowlist=("example.invalid",),
        ),
        scope,
    )
    platform.set_status("salesforce", IntegrationStatus.CONFIGURED, scope)
    platform.set_status("salesforce", IntegrationStatus.VALIDATED, scope)
    platform.set_status("salesforce", IntegrationStatus.ENABLED, scope)
    calls = 0

    def handler(item: Connector, payload: object) -> object:
        nonlocal calls
        calls += 1
        return {"connector": item.id, "accepted": bool(payload)}

    platform.register_handler(ConnectorType.REST_API, handler)
    first = platform.execute(connector.id, {"customer": 1}, scope, idempotency_key="k")
    second = platform.execute(connector.id, {"customer": 1}, scope, idempotency_key="k")
    assert first == second
    assert calls == 1
    platform.register_handler(
        ConnectorType.REST_API,
        lambda item, payload: (_ for _ in ()).throw(RuntimeError("down")),
    )
    with pytest.raises(RuntimeError, match="correlation_id"):
        platform.execute(connector.id, {}, scope, idempotency_key="failure")
    assert len(platform.dead_letters) == 1
    assert platform.metrics.snapshot()["integration_retries_total"] == 2


def test_webhooks_databases_storage_dashboard_and_security(
    configured: tuple[IntegrationPlatform, IntegrationScope],
) -> None:
    platform, scope = configured
    webhook = platform.add_webhook(
        Webhook(
            "hook-a",
            "salesforce",
            "inbound",
            scope.tenant,
            scope.workspace,
            "credential-a",
        ),
        scope,
    )
    body = b'{"event":"created"}'
    secret = b"resolved-outside-platform"
    signature = hmac.new(secret, body, hashlib.sha256).hexdigest()
    assert platform.verify_webhook(
        webhook.id, body, signature, "nonce-a", secret, scope
    )
    assert not platform.verify_webhook(
        webhook.id, body, signature, "nonce-a", secret, scope
    )
    platform.add_database(
        DatabaseConnection(
            "db-a",
            "salesforce",
            "sql",
            "credential-a",
            scope.tenant,
            scope.workspace,
        ),
        scope,
    )
    with pytest.raises(PermissionError, match="database:write"):
        platform.add_database(
            DatabaseConnection(
                "db-write",
                "salesforce",
                "sql",
                "credential-a",
                scope.tenant,
                scope.workspace,
                read_only=False,
            ),
            scope,
        )
    platform.add_storage(
        StorageConnection(
            "storage-a",
            "salesforce",
            "s3",
            "credential-a",
            scope.tenant,
            scope.workspace,
        ),
        scope,
    )
    dashboard = platform.dashboard(scope)
    assert set(dashboard) == set(SECTIONS)
    assert set(dashboard["metrics"]) == set(METRICS)
    assert "resolved-outside-platform" not in repr(platform.audit)
