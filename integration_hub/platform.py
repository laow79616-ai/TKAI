"""Secure, tenant-scoped Enterprise AI Integration Hub control plane."""

from __future__ import annotations

import json
import re
import secrets
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol, TypeVar

from .metrics import IntegrationHubMetrics


class IdentifiedScoped(Protocol):
    id: str
    tenant: str
    workspace: str


RecordT = TypeVar("RecordT", bound=IdentifiedScoped)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ConnectorCategory(str, Enum):
    CRM = "crm"
    ERP = "erp"
    HR = "hr"
    FINANCE = "finance"
    SUPPORT = "support"
    COLLABORATION = "collaboration"
    STORAGE = "storage"
    DATABASE = "database"
    MESSAGING = "messaging"
    CALENDAR = "calendar"
    EMAIL = "email"
    DOCUMENT_MANAGEMENT = "document_management"
    CUSTOM_INTERFACE = "custom_interface"


class ConnectorStatus(str, Enum):
    DRAFT = "draft"
    CONFIGURED = "configured"
    VALIDATED = "validated"
    ENABLED = "enabled"
    DISABLED = "disabled"
    FAILED = "failed"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ScheduleType(str, Enum):
    MANUAL = "manual"
    INTERVAL = "interval"
    CRON = "cron"
    EVENT_TRIGGERED = "event_triggered"
    WEBHOOK_TRIGGERED = "webhook_triggered"


@dataclass(frozen=True, slots=True)
class HubScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"integration_hub:read"})

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class Connector:
    id: str
    name: str
    provider: str
    category: ConnectorCategory
    version: str
    capabilities: tuple[str, ...]
    tenant: str
    workspace: str
    status: ConnectorStatus = ConnectorStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["category"] = self.category.value
        result["status"] = self.status.value
        return result


@dataclass(slots=True)
class CredentialReference:
    id: str
    tenant: str
    workspace: str
    secret_reference: str | None = None
    oauth2_reference: str | None = None
    api_key_reference: str | None = None
    certificate_reference: str | None = None
    service_account_reference: str | None = None
    rotation_interface: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        references = (
            self.secret_reference,
            self.oauth2_reference,
            self.api_key_reference,
            self.certificate_reference,
            self.service_account_reference,
        )
        if not any(references):
            raise ValueError("At least one credential reference is required.")
        if any(value and "://" not in value for value in references):
            raise ValueError("Credentials must be opaque references, never plaintext.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ConnectorInstance:
    id: str
    tenant: str
    workspace: str
    owner: str
    connector_id: str
    credential_reference: str
    configuration: dict[str, Any] = field(default_factory=dict)
    health: str = "unknown"
    status: ConnectorStatus = ConnectorStatus.CONFIGURED
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        return result


@dataclass(slots=True)
class Mapping:
    id: str
    tenant: str
    workspace: str
    source_schema: dict[str, str]
    target_schema: dict[str, str]
    field_mapping: dict[str, str]
    default_values: dict[str, Any] = field(default_factory=dict)
    required_fields: tuple[str, ...] = ()
    validation: dict[str, Any] = field(default_factory=dict)
    transformations: dict[str, str] = field(default_factory=dict)
    version: str = "1"

    def __post_init__(self) -> None:
        allowed = {
            "identity",
            "string",
            "integer",
            "number",
            "boolean",
            "lower",
            "upper",
        }
        if set(self.transformations.values()) - allowed:
            raise ValueError("Only declarative transformations are permitted.")

    def apply(self, payload: dict[str, Any]) -> dict[str, Any]:
        missing = set(self.required_fields) - payload.keys()
        if missing:
            raise ValueError(f"Required fields are missing: {sorted(missing)}")
        result = dict(self.default_values)
        for source, target in self.field_mapping.items():
            if source in payload:
                result[target] = self._transform(source, payload[source])
        return result

    def _transform(self, field_name: str, value: Any) -> Any:
        operation = self.transformations.get(field_name, "identity")
        transforms: dict[str, Callable[[Any], Any]] = {
            "identity": lambda item: item,
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "lower": lambda item: str(item).lower(),
            "upper": lambda item: str(item).upper(),
        }
        return transforms[operation](value)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class IntegrationPolicy:
    id: str
    tenant: str
    workspace: str
    rate_limit: int = 100
    timeout_seconds: float = 30
    retry_limit: int = 3
    backoff_seconds: float = 1
    circuit_breaker_threshold: int = 5
    idempotency: bool = True
    payload_limit_bytes: int = 1_048_576
    allowlist: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.rate_limit < 1 or self.timeout_seconds <= 0 or self.retry_limit < 0:
            raise ValueError("Policy limits must be positive.")
        if not 1 <= self.payload_limit_bytes <= 10_485_760:
            raise ValueError("Payload limit must be between 1 byte and 10 MiB.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Schedule:
    id: str
    tenant: str
    workspace: str
    type: ScheduleType
    expression: str | None = None
    missed_run_policy: str = "skip"
    timezone: str = "UTC"
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.missed_run_policy not in {"skip", "run_once", "catch_up"}:
            raise ValueError("Unsupported missed-run policy.")
        if (
            self.type in {ScheduleType.INTERVAL, ScheduleType.CRON}
            and not self.expression
        ):
            raise ValueError("Scheduled runs require an expression.")

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["type"] = self.type.value
        return result


@dataclass(slots=True)
class IntegrationFlow:
    id: str
    tenant: str
    workspace: str
    source: str
    target: str
    trigger: str
    mapping_id: str
    policy_id: str
    retry: bool = True
    dead_letter: bool = True
    schedule_id: str | None = None
    status: ConnectorStatus = ConnectorStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        return result


@dataclass(slots=True)
class IntegrationTemplate:
    id: str
    tenant: str
    workspace: str
    kind: str
    version: str
    definition: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.kind not in {"connector", "mapping", "flow"}:
            raise ValueError("Template kind must be connector, mapping, or flow.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class HealthRecord:
    instance_id: str
    tenant: str
    workspace: str
    connectivity: bool
    authentication: bool
    latency_seconds: float
    error_rate: float
    last_success: datetime | None = None
    last_failure: datetime | None = None
    status: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        for name in ("last_success", "last_failure"):
            value = result[name]
            result[name] = value.isoformat() if value else None
        return result


@dataclass(slots=True)
class FlowRun:
    id: str
    flow_id: str
    tenant: str
    workspace: str
    status: str
    attempts: int
    latency_seconds: float
    payload_size: int
    occurred_at: datetime = field(default_factory=utcnow)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["occurred_at"] = self.occurred_at.isoformat()
        return result


@dataclass(frozen=True, slots=True)
class AuditEntry:
    action: str
    actor: str
    tenant: str
    workspace: str
    occurred_at: datetime
    metadata: dict[str, Any]


class IntegrationHub:
    """In-memory reference control plane; registered adapters perform external I/O."""

    TRANSITIONS = {
        ConnectorStatus.DRAFT: {
            ConnectorStatus.CONFIGURED,
            ConnectorStatus.ARCHIVED,
            ConnectorStatus.DELETED,
        },
        ConnectorStatus.CONFIGURED: {
            ConnectorStatus.VALIDATED,
            ConnectorStatus.DISABLED,
            ConnectorStatus.FAILED,
        },
        ConnectorStatus.VALIDATED: {
            ConnectorStatus.ENABLED,
            ConnectorStatus.DISABLED,
            ConnectorStatus.FAILED,
        },
        ConnectorStatus.ENABLED: {
            ConnectorStatus.DISABLED,
            ConnectorStatus.FAILED,
            ConnectorStatus.DEPRECATED,
        },
        ConnectorStatus.DISABLED: {
            ConnectorStatus.CONFIGURED,
            ConnectorStatus.ENABLED,
            ConnectorStatus.ARCHIVED,
        },
        ConnectorStatus.FAILED: {
            ConnectorStatus.CONFIGURED,
            ConnectorStatus.DISABLED,
            ConnectorStatus.ARCHIVED,
        },
        ConnectorStatus.DEPRECATED: {
            ConnectorStatus.DISABLED,
            ConnectorStatus.ARCHIVED,
        },
        ConnectorStatus.ARCHIVED: {ConnectorStatus.DELETED},
        ConnectorStatus.DELETED: set(),
    }
    SECRET_KEYS = re.compile(
        r"(?:password|passwd|secret|token|api[_-]?key|authorization)", re.I
    )

    def __init__(self) -> None:
        self.connectors: dict[str, Connector] = {}
        self.credentials: dict[str, CredentialReference] = {}
        self.instances: dict[str, ConnectorInstance] = {}
        self.mappings: dict[str, Mapping] = {}
        self.policies: dict[str, IntegrationPolicy] = {}
        self.schedules: dict[str, Schedule] = {}
        self.flows: dict[str, IntegrationFlow] = {}
        self.templates: dict[str, IntegrationTemplate] = {}
        self.health_records: dict[str, HealthRecord] = {}
        self.runs: list[FlowRun] = []
        self.dead_letters: list[FlowRun] = []
        self.audit: list[AuditEntry] = []
        self.handlers: dict[str, Callable[[dict[str, Any]], Any]] = {}
        self.idempotency: dict[tuple[str, str], Any] = {}
        self.metrics = IntegrationHubMetrics()

    @staticmethod
    def _in_scope(record: Any, scope: HubScope) -> bool:
        return bool(
            record.tenant == scope.tenant and record.workspace == scope.workspace
        )

    def _get(
        self, records: dict[str, RecordT], record_id: str, scope: HubScope
    ) -> RecordT:
        record = records[record_id]
        if not self._in_scope(record, scope):
            raise PermissionError("Cross-tenant or cross-workspace access denied.")
        return record

    @staticmethod
    def _require(scope: HubScope, permission: str) -> None:
        if (
            permission not in scope.permissions
            and "integration_hub:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    def _audit(self, action: str, scope: HubScope, **metadata: Any) -> None:
        safe = {
            key: value
            for key, value in metadata.items()
            if not self.SECRET_KEYS.search(key)
        }
        self.audit.append(
            AuditEntry(
                action, scope.actor, scope.tenant, scope.workspace, utcnow(), safe
            )
        )

    def _add(
        self,
        records: dict[str, RecordT],
        record: RecordT,
        scope: HubScope,
        kind: str,
    ) -> RecordT:
        self._require(scope, "integration_hub:write")
        if not self._in_scope(record, scope):
            raise PermissionError("Cross-tenant or cross-workspace write denied.")
        if record.id in records:
            raise ValueError(f"{kind} already exists.")
        records[record.id] = record
        self._audit(f"{kind}.create", scope, record_id=record.id)
        return record

    def create_connector(self, connector: Connector, scope: HubScope) -> Connector:
        result = self._add(self.connectors, connector, scope, "connector")
        self.metrics.increment("integration_hub_connectors_total")
        return result

    def set_connector_status(
        self, connector_id: str, status: ConnectorStatus, scope: HubScope
    ) -> Connector:
        self._require(scope, "integration_hub:write")
        connector = self._get(self.connectors, connector_id, scope)
        if status not in self.TRANSITIONS[connector.status]:
            raise ValueError("Invalid connector lifecycle transition.")
        connector.status = status
        self._audit(
            "connector.status",
            scope,
            connector_id=connector_id,
            status=status.value,
        )
        return connector

    def add_credential(
        self, credential: CredentialReference, scope: HubScope
    ) -> CredentialReference:
        self._require(scope, "integration_hub:credentials")
        return self._add(self.credentials, credential, scope, "credential")

    def create_instance(
        self, instance: ConnectorInstance, scope: HubScope
    ) -> ConnectorInstance:
        self._get(self.connectors, instance.connector_id, scope)
        self._get(self.credentials, instance.credential_reference, scope)
        if self._contains_secret(instance.configuration):
            raise ValueError("Configuration must not contain plaintext secrets.")
        result = self._add(self.instances, instance, scope, "instance")
        self.metrics.increment("integration_hub_instances_total")
        return result

    def create_mapping(self, mapping: Mapping, scope: HubScope) -> Mapping:
        return self._add(self.mappings, mapping, scope, "mapping")

    def create_policy(
        self, policy: IntegrationPolicy, scope: HubScope
    ) -> IntegrationPolicy:
        return self._add(self.policies, policy, scope, "policy")

    def create_schedule(self, schedule: Schedule, scope: HubScope) -> Schedule:
        return self._add(self.schedules, schedule, scope, "schedule")

    def create_flow(self, flow: IntegrationFlow, scope: HubScope) -> IntegrationFlow:
        self._get(self.instances, flow.source, scope)
        self._get(self.instances, flow.target, scope)
        self._get(self.mappings, flow.mapping_id, scope)
        self._get(self.policies, flow.policy_id, scope)
        if flow.schedule_id:
            self._get(self.schedules, flow.schedule_id, scope)
        return self._add(self.flows, flow, scope, "flow")

    def import_template(
        self, template: IntegrationTemplate, scope: HubScope
    ) -> IntegrationTemplate:
        if self._contains_secret(template.definition):
            raise ValueError("Templates must not contain plaintext secrets.")
        return self._add(self.templates, template, scope, "template")

    def export_template(self, template_id: str, scope: HubScope) -> dict[str, Any]:
        self._require(scope, "integration_hub:read")
        return self._get(self.templates, template_id, scope).to_dict()

    def clone_template(
        self,
        template_id: str,
        clone_id: str,
        version: str,
        scope: HubScope,
    ) -> IntegrationTemplate:
        original = self._get(self.templates, template_id, scope)
        clone = IntegrationTemplate(
            clone_id,
            scope.tenant,
            scope.workspace,
            original.kind,
            version,
            dict(original.definition),
            {**original.metadata, "cloned_from": original.id},
        )
        return self.import_template(clone, scope)

    def register_handler(
        self,
        instance_id: str,
        handler: Callable[[dict[str, Any]], Any],
        scope: HubScope,
    ) -> None:
        self._require(scope, "integration_hub:execute")
        self._get(self.instances, instance_id, scope)
        self.handlers[instance_id] = handler

    def execute(
        self,
        flow_id: str,
        payload: dict[str, Any],
        scope: HubScope,
        *,
        idempotency_key: str | None = None,
    ) -> Any:
        self._require(scope, "integration_hub:execute")
        flow = self._get(self.flows, flow_id, scope)
        if flow.status is not ConnectorStatus.ENABLED:
            raise ValueError("Flow is not enabled.")
        policy = self._get(self.policies, flow.policy_id, scope)
        body = json.dumps(payload, separators=(",", ":"), default=str).encode()
        if len(body) > policy.payload_limit_bytes:
            raise ValueError("Payload exceeds configured size limit.")
        if self._contains_secret(payload):
            raise ValueError("Secrets are not allowed in integration payloads.")
        cache_key = (flow.id, idempotency_key or "")
        if policy.idempotency and idempotency_key and cache_key in self.idempotency:
            return self.idempotency[cache_key]
        mapped = self._get(self.mappings, flow.mapping_id, scope).apply(payload)
        handler = self.handlers.get(flow.target)
        if handler is None:
            raise RuntimeError("No target connector adapter is registered.")
        attempts = 0
        started = utcnow()
        error: Exception | None = None
        for attempts in range(1, policy.retry_limit + 2):
            try:
                result = handler(mapped)
                latency = (utcnow() - started).total_seconds()
                self._record_run(flow, scope, "success", attempts, latency, len(body))
                if idempotency_key:
                    self.idempotency[cache_key] = result
                return result
            except Exception as exc:
                error = exc
                if attempts <= policy.retry_limit:
                    self.metrics.increment("integration_hub_retries_total")
        latency = (utcnow() - started).total_seconds()
        run = self._record_run(
            flow, scope, "failed", attempts, latency, len(body), str(error)
        )
        if flow.dead_letter:
            self.dead_letters.append(run)
            self.metrics.increment("integration_hub_dead_letter_total")
        raise RuntimeError(f"Integration flow failed; run_id={run.id}") from error

    def _record_run(
        self,
        flow: IntegrationFlow,
        scope: HubScope,
        status: str,
        attempts: int,
        latency: float,
        size: int,
        error: str | None = None,
    ) -> FlowRun:
        run = FlowRun(
            secrets.token_hex(12),
            flow.id,
            scope.tenant,
            scope.workspace,
            status,
            attempts,
            latency,
            size,
            error=error,
        )
        self.runs.append(run)
        self.metrics.increment("integration_hub_runs_total")
        self.metrics.set("integration_hub_latency_seconds", latency)
        if status == "failed":
            self.metrics.increment("integration_hub_failures_total")
        self._audit("flow.run", scope, flow_id=flow.id, run_id=run.id, status=status)
        return run

    def record_health(self, health: HealthRecord, scope: HubScope) -> HealthRecord:
        self._require(scope, "integration_hub:health")
        instance = self._get(self.instances, health.instance_id, scope)
        healthy = (
            health.connectivity and health.authentication and health.error_rate < 0.05
        )
        health.status = "healthy" if healthy else "unhealthy"
        instance.health = health.status
        self.health_records[health.instance_id] = health
        self.metrics.set(
            "integration_hub_healthy_connectors",
            sum(
                item.status == "healthy"
                for item in self.health_records.values()
                if self._in_scope(item, scope)
            ),
        )
        return health

    def dashboard(self, scope: HubScope) -> dict[str, Any]:
        self._require(scope, "integration_hub:read")

        def scoped(values: Any) -> list[Any]:
            return [item for item in values if self._in_scope(item, scope)]

        connectors = scoped(self.connectors.values())
        instances = scoped(self.instances.values())
        runs = scoped(self.runs)
        successes = sum(run.status == "success" for run in runs)
        failures = sum(run.status == "failed" for run in runs)
        return {
            "catalog": [item.to_dict() for item in connectors],
            "connectors": [item.to_dict() for item in connectors],
            "instances": [item.to_dict() for item in instances],
            "mappings": [item.to_dict() for item in scoped(self.mappings.values())],
            "flows": [item.to_dict() for item in scoped(self.flows.values())],
            "credentials": [
                item.to_dict() for item in scoped(self.credentials.values())
            ],
            "health": [item.to_dict() for item in scoped(self.health_records.values())],
            "schedules": [item.to_dict() for item in scoped(self.schedules.values())],
            "failures": [item.to_dict() for item in runs if item.status == "failed"],
            "dead_letter": [item.to_dict() for item in scoped(self.dead_letters)],
            "analytics": {
                "runs": len(runs),
                "successes": successes,
                "failures": failures,
                "retries": self.metrics.snapshot()["integration_hub_retries_total"],
                "latency": (
                    sum(item.latency_seconds for item in runs) / len(runs)
                    if runs
                    else 0
                ),
                "throughput": len(runs),
                "payload_size": sum(item.payload_size for item in runs),
                "connector_health": {item.id: item.health for item in instances},
            },
            "metrics": self.metrics.snapshot(),
        }

    @classmethod
    def _contains_secret(cls, value: Any) -> bool:
        if isinstance(value, dict):
            return any(
                cls.SECRET_KEYS.search(str(key)) or cls._contains_secret(item)
                for key, item in value.items()
            )
        if isinstance(value, (list, tuple)):
            return any(cls._contains_secret(item) for item in value)
        return False


EnterpriseAIIntegrationHub = IntegrationHub
