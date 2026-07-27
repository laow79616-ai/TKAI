"""Secure tenant-scoped Enterprise AI Integration Platform reference control plane."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from time import monotonic
from typing import Any, Protocol

from .metrics import IntegrationMetrics


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IntegrationStatus(str, Enum):
    DRAFT = "draft"
    CONFIGURED = "configured"
    VALIDATED = "validated"
    ENABLED = "enabled"
    DISABLED = "disabled"
    FAILED = "failed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ConnectorType(str, Enum):
    REST_API = "rest_api"
    GRAPHQL = "graphql"
    WEBHOOK = "webhook"
    DATABASE = "database"
    MESSAGE_QUEUE = "message_queue"
    OBJECT_STORAGE = "object_storage"
    EMAIL = "email"
    CALENDAR = "calendar"
    FILE_TRANSFER = "file_transfer"
    CUSTOM = "custom"


class CredentialType(str, Enum):
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    SERVICE_ACCOUNT = "service_account"
    CERTIFICATE = "certificate"
    SECRET_STORE = "secret_store"


class EnterpriseSystem(str, Enum):
    CRM = "crm"
    ERP = "erp"
    HR = "hr"
    FINANCE = "finance"
    SUPPORT = "support"
    DOCUMENT_MANAGEMENT = "document_management"
    COLLABORATION = "collaboration"


@dataclass(frozen=True, slots=True)
class IntegrationScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"integration:read"})

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class Integration:
    id: str
    name: str
    description: str
    provider: str
    category: str
    owner: str
    tenant: str
    workspace: str
    status: IntegrationStatus = IntegrationStatus.DRAFT
    version: str = "1.0"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class CredentialReference:
    id: str
    type: CredentialType
    reference: str
    tenant: str
    workspace: str
    rotated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.reference.startswith(("secret://", "vault://", "kms://")):
            raise ValueError("Credentials must be opaque secret-store references.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "reference": self.reference,
            "tenant": self.tenant,
            "workspace": self.workspace,
            "rotated_at": self.rotated_at.isoformat() if self.rotated_at else None,
        }


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    attempts: int = 3
    backoff_seconds: float = 0
    timeout_seconds: float = 30

    def __post_init__(self) -> None:
        if not 1 <= self.attempts <= 10:
            raise ValueError("Retry attempts must be between 1 and 10.")
        if self.backoff_seconds < 0 or not 0 < self.timeout_seconds <= 300:
            raise ValueError("Backoff or timeout is outside the bounded policy.")


@dataclass(slots=True)
class Connector:
    id: str
    integration_id: str
    name: str
    type: ConnectorType
    tenant: str
    workspace: str
    credential_reference_id: str | None = None
    base_url: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    request_mapping: dict[str, str] = field(default_factory=dict)
    response_mapping: dict[str, str] = field(default_factory=dict)
    pagination: dict[str, Any] = field(default_factory=dict)
    rate_limit: int = 100
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    allowlist: tuple[str, ...] = ()
    max_request_bytes: int = 1_048_576
    max_response_bytes: int = 5_242_880

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["type"] = self.type.value
        return value


@dataclass(slots=True)
class Webhook:
    id: str
    integration_id: str
    direction: str
    tenant: str
    workspace: str
    signing_secret_reference_id: str
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    max_body_bytes: int = 1_048_576
    deliveries: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.direction not in {"inbound", "outbound"}:
            raise ValueError("Webhook direction must be inbound or outbound.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EventSubscription:
    id: str
    integration_id: str
    topic: str
    tenant: str
    workspace: str
    filters: dict[str, Any] = field(default_factory=dict)
    schema: dict[str, Any] = field(default_factory=dict)
    ordering_key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DatabaseConnection:
    id: str
    integration_id: str
    kind: str
    connection_reference_id: str
    tenant: str
    workspace: str
    read_only: bool = True
    query_limit: int = 1000
    transactions_enabled: bool = False

    def __post_init__(self) -> None:
        if self.kind not in {"sql", "nosql"}:
            raise ValueError("Database kind must be sql or nosql.")
        if not 1 <= self.query_limit <= 10_000:
            raise ValueError("Query limit must be between 1 and 10000.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class StorageConnection:
    id: str
    integration_id: str
    provider: str
    credential_reference_id: str
    tenant: str
    workspace: str
    retention_days: int = 30
    max_file_bytes: int = 10_485_760

    def __post_init__(self) -> None:
        if self.provider not in {"s3", "azure_blob", "gcs"}:
            raise ValueError("Unsupported storage provider.")
        if self.retention_days < 1 or self.max_file_bytes < 1:
            raise ValueError("Storage limits must be positive.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DeadLetter:
    id: str
    resource_type: str
    resource_id: str
    tenant: str
    workspace: str
    reason: str
    correlation_id: str
    occurred_at: datetime

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["occurred_at"] = self.occurred_at.isoformat()
        return value


@dataclass(frozen=True, slots=True)
class AuditEntry:
    action: str
    actor: str
    tenant: str
    workspace: str
    occurred_at: datetime
    metadata: dict[str, Any]


class QueueInterface(Protocol):
    def publish(self, topic: str, payload: Mapping[str, Any]) -> str: ...

    def subscribe(
        self,
        topic: str,
        consumer_group: str,
        handler: Callable[[Mapping[str, Any]], None],
    ) -> None: ...

    def acknowledge(self, message_id: str) -> None: ...

    def depth(self, topic: str) -> int: ...


class ObjectStorageInterface(Protocol):
    def upload(self, reference: str, content: bytes) -> None: ...

    def download(self, reference: str) -> bytes: ...


ConnectorHandler = Callable[[Connector, Mapping[str, Any]], Any]


class IntegrationPlatform:
    """Bounded reference implementation with isolation, RBAC, audit and metrics."""

    TRANSITIONS = {
        IntegrationStatus.DRAFT: {
            IntegrationStatus.CONFIGURED,
            IntegrationStatus.ARCHIVED,
            IntegrationStatus.DELETED,
        },
        IntegrationStatus.CONFIGURED: {
            IntegrationStatus.VALIDATED,
            IntegrationStatus.FAILED,
            IntegrationStatus.ARCHIVED,
        },
        IntegrationStatus.VALIDATED: {
            IntegrationStatus.ENABLED,
            IntegrationStatus.FAILED,
            IntegrationStatus.ARCHIVED,
        },
        IntegrationStatus.ENABLED: {
            IntegrationStatus.DISABLED,
            IntegrationStatus.FAILED,
            IntegrationStatus.ARCHIVED,
        },
        IntegrationStatus.DISABLED: {
            IntegrationStatus.ENABLED,
            IntegrationStatus.ARCHIVED,
            IntegrationStatus.DELETED,
        },
        IntegrationStatus.FAILED: {
            IntegrationStatus.CONFIGURED,
            IntegrationStatus.DISABLED,
            IntegrationStatus.ARCHIVED,
        },
        IntegrationStatus.ARCHIVED: {IntegrationStatus.DELETED},
        IntegrationStatus.DELETED: set(),
    }

    def __init__(self) -> None:
        self.integrations: dict[str, Integration] = {}
        self.connectors: dict[str, Connector] = {}
        self.credentials: dict[str, CredentialReference] = {}
        self.webhooks: dict[str, Webhook] = {}
        self.events: dict[str, EventSubscription] = {}
        self.databases: dict[str, DatabaseConnection] = {}
        self.storage: dict[str, StorageConnection] = {}
        self.dead_letters: list[DeadLetter] = []
        self.audit: list[AuditEntry] = []
        self.metrics = IntegrationMetrics()
        self._handlers: dict[ConnectorType, ConnectorHandler] = {}
        self._idempotency: dict[str, Any] = {}
        self._replay_nonces: set[str] = set()

    @staticmethod
    def _check(record: Any, scope: IntegrationScope) -> None:
        if record.tenant != scope.tenant or record.workspace != scope.workspace:
            raise PermissionError("Cross-scope integration access denied.")

    @staticmethod
    def _require(scope: IntegrationScope, permission: str) -> None:
        if (
            permission not in scope.permissions
            and "integration:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    def _audit(self, action: str, scope: IntegrationScope, **metadata: Any) -> None:
        self.audit.append(
            AuditEntry(
                action, scope.actor, scope.tenant, scope.workspace, utcnow(), metadata
            )
        )

    def _scoped(self, values: Any, scope: IntegrationScope) -> list[Any]:
        self._require(scope, "integration:read")
        return [
            value
            for value in values
            if value.tenant == scope.tenant and value.workspace == scope.workspace
        ]

    def create_integration(
        self, integration: Integration, scope: IntegrationScope
    ) -> Integration:
        self._require(scope, "integration:write")
        self._check(integration, scope)
        if integration.id in self.integrations:
            raise ValueError("Integration already exists.")
        self.integrations[integration.id] = integration
        self.metrics.increment("integrations_total")
        self._audit("integration.create", scope, integration_id=integration.id)
        return integration

    def list_integrations(self, scope: IntegrationScope) -> list[Integration]:
        return self._scoped(self.integrations.values(), scope)

    def set_status(
        self, integration_id: str, status: IntegrationStatus, scope: IntegrationScope
    ) -> Integration:
        self._require(scope, "integration:write")
        integration = self.integrations[integration_id]
        self._check(integration, scope)
        if status not in self.TRANSITIONS[integration.status]:
            transition = f"{integration.status.value} -> {status.value}"
            raise ValueError(f"Invalid lifecycle transition: {transition}")
        integration.status = status
        self._audit(
            "integration.status",
            scope,
            integration_id=integration_id,
            status=status.value,
        )
        return integration

    def add_credential(
        self, credential: CredentialReference, scope: IntegrationScope
    ) -> CredentialReference:
        self._require(scope, "integration:credentials")
        self._check(credential, scope)
        self.credentials[credential.id] = credential
        self._audit("credential.reference.create", scope, credential_id=credential.id)
        return credential

    def rotate_credential(self, credential_id: str, scope: IntegrationScope) -> None:
        self._require(scope, "integration:credentials")
        credential = self.credentials[credential_id]
        self._check(credential, scope)
        credential.rotated_at = utcnow()
        self._audit("credential.reference.rotate", scope, credential_id=credential_id)

    def add_connector(self, connector: Connector, scope: IntegrationScope) -> Connector:
        self._require(scope, "integration:write")
        self._check(connector, scope)
        integration = self.integrations[connector.integration_id]
        self._check(integration, scope)
        if connector.rate_limit < 1 or connector.max_request_bytes < 1:
            raise ValueError("Connector limits must be positive.")
        if connector.credential_reference_id:
            credential = self.credentials[connector.credential_reference_id]
            self._check(credential, scope)
        self.connectors[connector.id] = connector
        self._audit("connector.create", scope, connector_id=connector.id)
        return connector

    def add_webhook(self, webhook: Webhook, scope: IntegrationScope) -> Webhook:
        self._require(scope, "integration:write")
        self._check(webhook, scope)
        credential = self.credentials[webhook.signing_secret_reference_id]
        self._check(credential, scope)
        self.webhooks[webhook.id] = webhook
        return webhook

    def add_event(
        self, subscription: EventSubscription, scope: IntegrationScope
    ) -> EventSubscription:
        self._require(scope, "integration:write")
        self._check(subscription, scope)
        self.events[subscription.id] = subscription
        return subscription

    def add_database(
        self, database: DatabaseConnection, scope: IntegrationScope
    ) -> DatabaseConnection:
        self._require(scope, "integration:write")
        self._check(database, scope)
        if not database.read_only or database.transactions_enabled:
            self._require(scope, "integration:database:write")
        credential = self.credentials[database.connection_reference_id]
        self._check(credential, scope)
        self.databases[database.id] = database
        return database

    def add_storage(
        self, storage: StorageConnection, scope: IntegrationScope
    ) -> StorageConnection:
        self._require(scope, "integration:write")
        self._check(storage, scope)
        credential = self.credentials[storage.credential_reference_id]
        self._check(credential, scope)
        self.storage[storage.id] = storage
        return storage

    def register_handler(
        self, connector_type: ConnectorType, handler: ConnectorHandler
    ) -> None:
        self._handlers[connector_type] = handler

    def execute(
        self,
        connector_id: str,
        payload: Mapping[str, Any],
        scope: IntegrationScope,
        *,
        idempotency_key: str,
    ) -> Any:
        self._require(scope, "integration:execute")
        connector = self.connectors[connector_id]
        self._check(connector, scope)
        integration = self.integrations[connector.integration_id]
        if integration.status is not IntegrationStatus.ENABLED:
            raise ValueError("Only enabled integrations may execute.")
        if len(repr(dict(payload)).encode()) > connector.max_request_bytes:
            raise ValueError("Request exceeds the configured size bound.")
        if idempotency_key in self._idempotency:
            return self._idempotency[idempotency_key]
        handler = self._handlers.get(connector.type)
        if handler is None:
            raise NotImplementedError(
                "No bounded connector implementation is registered."
            )
        started = monotonic()
        self.metrics.increment("integration_requests_total")
        error: Exception | None = None
        for attempt in range(connector.retry_policy.attempts):
            try:
                result = handler(connector, payload)
                if len(repr(result).encode()) > connector.max_response_bytes:
                    raise ValueError("Response exceeds the configured size bound.")
                self._idempotency[idempotency_key] = result
                self.metrics.increment(
                    "integration_latency_seconds", monotonic() - started
                )
                return result
            except Exception as current:
                error = current
                if attempt + 1 < connector.retry_policy.attempts:
                    self.metrics.increment("integration_retries_total")
        self.metrics.increment("integration_failures_total")
        correlation_id = secrets.token_hex(12)
        self.dead_letters.append(
            DeadLetter(
                secrets.token_hex(12),
                "connector",
                connector.id,
                scope.tenant,
                scope.workspace,
                str(error),
                correlation_id,
                utcnow(),
            )
        )
        self.metrics.increment("dead_letter_total")
        self.metrics.increment("integration_latency_seconds", monotonic() - started)
        raise RuntimeError(
            f"Integration failed; correlation_id={correlation_id}"
        ) from error

    def verify_webhook(
        self,
        webhook_id: str,
        body: bytes,
        signature: str,
        nonce: str,
        secret: bytes,
        scope: IntegrationScope,
    ) -> bool:
        self._require(scope, "integration:webhook")
        webhook = self.webhooks[webhook_id]
        self._check(webhook, scope)
        self.metrics.increment("webhook_deliveries_total")
        if len(body) > webhook.max_body_bytes or nonce in self._replay_nonces:
            self.metrics.increment("webhook_failures_total")
            return False
        expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
        valid = hmac.compare_digest(expected, signature)
        if valid:
            self._replay_nonces.add(nonce)
        else:
            self.metrics.increment("webhook_failures_total")
        webhook.deliveries.append(
            {
                "correlation_id": nonce,
                "succeeded": valid,
                "delivered_at": utcnow().isoformat(),
            }
        )
        return valid

    def health(self, scope: IntegrationScope) -> list[dict[str, Any]]:
        return [
            {
                "integration_id": item.id,
                "status": item.status.value,
                "healthy": item.status is IntegrationStatus.ENABLED,
            }
            for item in self.list_integrations(scope)
        ]

    def dashboard(self, scope: IntegrationScope) -> dict[str, Any]:
        collections = {
            "integrations": self.integrations.values(),
            "connectors": self.connectors.values(),
            "credentials": self.credentials.values(),
            "webhooks": self.webhooks.values(),
            "events": self.events.values(),
            "messaging": (),
            "databases": self.databases.values(),
            "storage": self.storage.values(),
        }
        result = {
            name: [item.to_dict() for item in self._scoped(values, scope)]
            for name, values in collections.items()
        }
        result["health"] = self.health(scope)
        result["failures"] = [
            item.to_dict() for item in self._scoped(self.dead_letters, scope)
        ]
        result["metrics"] = self.metrics.snapshot()
        return result


EnterpriseAIIntegrationPlatform = IntegrationPlatform

__all__ = (
    "AuditEntry",
    "Connector",
    "ConnectorHandler",
    "ConnectorType",
    "CredentialReference",
    "CredentialType",
    "DatabaseConnection",
    "DeadLetter",
    "EnterpriseAIIntegrationPlatform",
    "EnterpriseSystem",
    "EventSubscription",
    "Integration",
    "IntegrationPlatform",
    "IntegrationScope",
    "IntegrationStatus",
    "ObjectStorageInterface",
    "QueueInterface",
    "RetryPolicy",
    "StorageConnection",
    "Webhook",
    "utcnow",
)
