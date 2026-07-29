"""Bounded, local-only V7 unified data and storage metadata framework."""

from __future__ import annotations

from collections import Counter
from threading import RLock
from typing import TypeVar

from .contracts import (
    ArchivePlan,
    DataModel,
    DataQuery,
    DataRecord,
    DataSchema,
    IndexDefinition,
    MigrationAssessment,
    RepositoryDefinition,
    RetentionPolicy,
    Scope,
    Snapshot,
    StorageAdapter,
    TransactionMetadata,
    VersionMetadata,
    payload_digest,
    serialize,
)

T = TypeVar("T")
MAX_REGISTRY_ITEMS = 1000
METRIC_NAMES = (
    "v7_data_models_total",
    "v7_data_schemas_total",
    "v7_data_repositories_total",
    "v7_data_adapters_total",
    "v7_data_queries_total",
    "v7_data_query_failures_total",
    "v7_data_records_validated_total",
    "v7_data_validation_failures_total",
    "v7_data_snapshots_total",
    "v7_data_integrity_failures_total",
    "v7_data_migration_assessments_total",
    "v7_data_archive_plans_total",
    "v7_data_query_latency_seconds",
    "v7_data_validation_latency_seconds",
    "v7_data_health_status",
)


class DataFrameworkError(RuntimeError):
    pass


class DuplicateReferenceError(DataFrameworkError):
    pass


class ValidationError(DataFrameworkError):
    pass


class MetadataRegistry:
    def __init__(self) -> None:
        self._items: dict[str, object] = {}
        self._lock = RLock()

    def register(self, key: str, item: T) -> T:
        with self._lock:
            if key in self._items:
                raise DuplicateReferenceError(f"already registered: {key}")
            if len(self._items) >= MAX_REGISTRY_ITEMS:
                raise DataFrameworkError("registry capacity reached")
            self._items[key] = item
        return item

    def values(self, expected: type[T], scope: Scope | None = None) -> tuple[T, ...]:
        values = tuple(
            item for item in self._items.values() if isinstance(item, expected)
        )
        if scope:
            values = tuple(
                item for item in values if getattr(item, "scope", None) == scope
            )
        return values[:MAX_REGISTRY_ITEMS]


class UnifiedDataFramework:
    """Coordinate metadata without migration, deletion, archival, or remote I/O."""

    PROJECTIONS = (
        "catalog",
        "models",
        "records",
        "schemas",
        "registry",
        "repositories",
        "adapters",
        "storage",
        "queries",
        "filters",
        "sorting",
        "pagination",
        "indexing",
        "transactions",
        "snapshots",
        "versions",
        "retention",
        "archival",
        "integrity",
        "validation",
        "migration",
        "compatibility",
        "health",
        "metrics",
        "audit",
        "lifecycle",
    )

    def __init__(self) -> None:
        self.models = MetadataRegistry()
        self.records = MetadataRegistry()
        self.schemas = MetadataRegistry()
        self.repositories = MetadataRegistry()
        self.adapters = MetadataRegistry()
        self.queries = MetadataRegistry()
        self.indexes = MetadataRegistry()
        self.transactions = MetadataRegistry()
        self.snapshots = MetadataRegistry()
        self.versions = MetadataRegistry()
        self.retention = MetadataRegistry()
        self.archival = MetadataRegistry()
        self.migrations = MetadataRegistry()
        self.audit: list[dict[str, object]] = []
        self.events: list[dict[str, object]] = []
        self.metrics: Counter[str] = Counter({name: 0 for name in METRIC_NAMES})
        self.metrics["v7_data_health_status"] = 1

    def register_schema(self, item: DataSchema) -> DataSchema:
        return self._register(
            self.schemas, f"{item.schema_id}:{item.version}", item, "schemas"
        )

    def register_repository(self, item: RepositoryDefinition) -> RepositoryDefinition:
        return self._register(
            self.repositories,
            f"{item.repository_id}:{item.version}",
            item,
            "repositories",
        )

    def register_adapter(self, item: StorageAdapter) -> StorageAdapter:
        return self._register(
            self.adapters, f"{item.adapter_id}:{item.version}", item, "adapters"
        )

    def register_model(self, item: DataModel) -> DataModel:
        self._require_reference(
            self.schemas, item.schema_reference, DataSchema, item.scope
        )
        self._require_reference(
            self.repositories,
            item.repository_reference,
            RepositoryDefinition,
            item.scope,
        )
        self._require_reference(
            self.adapters, item.storage_reference, StorageAdapter, item.scope
        )
        return self._register(
            self.models, f"{item.model_id}:{item.version}", item, "models"
        )

    def validate_record(
        self, item: DataRecord, payload: bytes | None = None
    ) -> DataRecord:
        model = self._find_model(item.model_reference, item.scope)
        schema = self._find_schema(model.schema_reference, item.scope)
        if schema.version != item.schema_version:
            self._failure("validation", item.record_id, item.scope)
            raise ValidationError("record schema version does not match")
        if payload is not None and payload_digest(payload) != item.payload_hash:
            self._failure("integrity", item.record_id, item.scope)
            raise ValidationError("payload hash does not match")
        self.records.register(f"{item.record_id}:{item.version}", item)
        self.metrics["v7_data_records_validated_total"] += 1
        self._record("record-validated", item.record_id, item.scope)
        return item

    def register_query(self, item: DataQuery) -> DataQuery:
        model = self._find_model(item.model_reference, item.scope)
        schema = self._find_schema(model.schema_reference, item.scope)
        fields = schema.allowed_fields
        used = {value.field for value in item.filters}
        used.update(value.field for value in item.sort_order)
        used.update(item.projection_fields)
        if not used.issubset(fields):
            self._failure("query", item.query_id, item.scope)
            raise ValidationError(
                f"query fields are not allowlisted: {sorted(used - fields)}"
            )
        return self._register(self.queries, item.query_id, item, "queries")

    def register_index(self, item: IndexDefinition) -> IndexDefinition:
        if not item.planning_only:
            raise ValidationError("production index mutation is prohibited")
        return self._register(
            self.indexes, f"{item.index_id}:{item.version}", item, "indexes"
        )

    def register_transaction(self, item: TransactionMetadata) -> TransactionMetadata:
        if not item.simulated or item.distributed:
            raise ValidationError(
                "only local transaction metadata simulation is supported"
            )
        return self._register(
            self.transactions, item.transaction_id, item, "transactions"
        )

    def register_snapshot(self, item: Snapshot) -> Snapshot:
        return self._register(
            self.snapshots, f"{item.snapshot_id}:{item.version}", item, "snapshots"
        )

    def register_version(self, item: VersionMetadata) -> VersionMetadata:
        return self._register(
            self.versions, f"{item.subject_reference}:{item.version}", item, "versions"
        )

    def register_retention_policy(self, item: RetentionPolicy) -> RetentionPolicy:
        if item.destructive_purge:
            raise ValidationError("destructive purge is prohibited")
        return self._register(
            self.retention, f"{item.policy_id}:{item.version}", item, "retention"
        )

    def plan_archive(self, item: ArchivePlan) -> ArchivePlan:
        if item.executable:
            raise ValidationError("automatic archival is prohibited")
        return self._register(self.archival, item.plan_id, item, "archive_plans")

    def assess_migration(self, item: MigrationAssessment) -> MigrationAssessment:
        if item.executable:
            raise ValidationError("automatic migration is prohibited")
        return self._register(
            self.migrations, item.assessment_id, item, "migration_assessments"
        )

    def projection(self, section: str, scope: Scope) -> object:
        maps: dict[str, object] = {
            "models": self.models.values(DataModel, scope),
            "records": self.records.values(DataRecord, scope),
            "schemas": self.schemas.values(DataSchema, scope),
            "repositories": self.repositories.values(RepositoryDefinition, scope),
            "adapters": self.adapters.values(StorageAdapter, scope),
            "storage": self.adapters.values(StorageAdapter, scope),
            "queries": self.queries.values(DataQuery, scope),
            "filters": self._nested(DataQuery, scope, "filters"),
            "sorting": self._nested(DataQuery, scope, "sort_order"),
            "pagination": self._nested(DataQuery, scope, "pagination"),
            "indexing": self.indexes.values(IndexDefinition, scope),
            "transactions": self.transactions.values(TransactionMetadata, scope),
            "snapshots": self.snapshots.values(Snapshot, scope),
            "versions": self.versions.values(VersionMetadata),
            "retention": self.retention.values(RetentionPolicy, scope),
            "archival": self.archival.values(ArchivePlan, scope),
            "migration": self.migrations.values(MigrationAssessment, scope),
            "metrics": dict(self.metrics),
            "audit": tuple(
                event for event in self.audit if event["scope"] == serialize(scope)
            ),
            "lifecycle": tuple(
                item.lifecycle for item in self.models.values(DataModel, scope)
            ),
            "compatibility": self.compatibility(),
            "health": self.health(scope),
            "integrity": self._status(scope, "integrity"),
            "validation": self._status(scope, "validation"),
        }
        maps["registry"] = {
            key: len(value) for key, value in maps.items() if isinstance(value, tuple)
        }
        maps["catalog"] = {
            "models": maps["models"],
            "schemas": maps["schemas"],
            "repositories": maps["repositories"],
            "storage": maps["storage"],
        }
        if section not in maps:
            raise DataFrameworkError(f"unknown projection: {section}")
        return serialize(maps[section])

    def compatibility(self) -> dict[str, object]:
        return {
            "v6": True,
            "v7_frameworks": (
                "foundation",
                "capabilities",
                "service-mesh",
                "event-fabric",
                "state",
                "workflow",
                "resource",
                "security",
                "observability",
                "configuration",
                "extension",
                "ai",
            ),
            "external_networking": False,
            "destructive_operations": False,
        }

    def health(self, scope: Scope) -> dict[str, object]:
        return {
            "status": "healthy",
            "ready": True,
            "live": True,
            "models": len(self.models.values(DataModel, scope)),
            "schemas": len(self.schemas.values(DataSchema, scope)),
            "repositories": len(self.repositories.values(RepositoryDefinition, scope)),
            "adapters": len(self.adapters.values(StorageAdapter, scope)),
            "external_connections_enabled": False,
            "automatic_migration_enabled": False,
        }

    def _nested(
        self, expected: type[DataQuery], scope: Scope, name: str
    ) -> tuple[object, ...]:
        return tuple(
            getattr(item, name) for item in self.queries.values(expected, scope)
        )

    def _status(self, scope: Scope, name: str) -> dict[str, object]:
        return {
            "status": "healthy",
            "failures": self.metrics[f"v7_data_{name}_failures_total"],
        }

    def _find_model(self, reference: str, scope: Scope) -> DataModel:
        return self._find(self.models, reference, DataModel, scope)

    def _find_schema(self, reference: str, scope: Scope) -> DataSchema:
        return self._find(self.schemas, reference, DataSchema, scope)

    def _find(
        self,
        registry: MetadataRegistry,
        reference: str,
        expected: type[T],
        scope: Scope,
    ) -> T:
        matches = [
            item
            for item in registry.values(expected, scope)
            if reference
            in {
                getattr(item, "model_id", ""),
                getattr(item, "schema_id", ""),
                getattr(item, "repository_id", ""),
                getattr(item, "adapter_id", ""),
                f"{getattr(item, 'schema_id', '')}:{getattr(item, 'version', '')}",
                f"{getattr(item, 'repository_id', '')}:{getattr(item, 'version', '')}",
                f"{getattr(item, 'adapter_id', '')}:{getattr(item, 'version', '')}",
            }
        ]
        if not matches:
            raise ValidationError(f"unregistered or cross-scope reference: {reference}")
        return matches[0]

    def _require_reference(
        self,
        registry: MetadataRegistry,
        reference: str,
        expected: type[T],
        scope: Scope,
    ) -> None:
        self._find(registry, reference, expected, scope)

    def _register(self, store: MetadataRegistry, key: str, item: T, metric: str) -> T:
        value = store.register(key, item)
        self.metrics[f"v7_data_{metric}_total"] += 1
        scope = getattr(item, "scope", None)
        if not isinstance(scope, Scope):
            raise ValidationError("registered metadata requires an isolated scope")
        self._record(f"{metric.rstrip('s')}-registered", key, scope)
        return value

    def _failure(self, kind: str, subject: str, scope: Scope) -> None:
        self.metrics[f"v7_data_{kind}_failures_total"] += 1
        self._record(f"{kind}-failed", subject, scope)

    def _record(self, action: str, subject: str, scope: Scope) -> None:
        event = {"action": action, "subject": subject, "scope": serialize(scope)}
        self.audit.append(event)
        self.events.append({"fabric": "v7.event_fabric", **event})


GLOBAL_DATA_FRAMEWORK = UnifiedDataFramework()
__all__ = tuple(name for name in globals() if not name.startswith("_"))
