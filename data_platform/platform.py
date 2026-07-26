"""Enterprise AI Data Platform domain and service."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, replace
from enum import Enum
from typing import Any, Protocol


class DatasetStatus(str, Enum):
    DRAFT = "draft"
    IMPORTED = "imported"
    VALIDATED = "validated"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Classification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class PipelineStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class DataScope:
    tenant: str
    workspace: str

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace:
            raise ValueError("Tenant and workspace are required.")


@dataclass(slots=True)
class Dataset:
    id: str
    name: str
    description: str
    owner: str
    tenant: str
    workspace: str
    classification: Classification
    version: str
    schema: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    status: DatasetStatus = DatasetStatus.DRAFT
    tags: tuple[str, ...] = ()
    domain: str = ""

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["classification"] = self.classification.value
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class Pipeline:
    id: str
    name: str
    tenant: str
    workspace: str
    source: str
    target: str
    transformations: tuple[str, ...] = ()
    schedule: str | None = None
    max_retries: int = 3
    checkpoint: str | None = None
    attempts: int = 0
    status: PipelineStatus = PipelineStatus.DRAFT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(frozen=True, slots=True)
class LineageEdge:
    source: str
    target: str
    pipeline: str
    transformation: str
    dependencies: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class QualityRule:
    name: str
    dimension: str
    field: str | None = None
    threshold: float = 1.0


@dataclass(frozen=True, slots=True)
class QualityResult:
    dataset_id: str
    scores: dict[str, float]
    failures: tuple[str, ...]
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Storage(Protocol):
    def put(self, key: str, value: bytes) -> None: ...
    def get(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...


class MemoryStorage:
    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}

    def put(self, key: str, value: bytes) -> None:
        self.values[key] = bytes(value)

    def get(self, key: str) -> bytes:
        if key not in self.values:
            raise KeyError(f"Storage object not found: {key}")
        return self.values[key]

    def delete(self, key: str) -> None:
        self.values.pop(key, None)


class ObjectStorage(MemoryStorage):
    pass


class SQLStorage(MemoryStorage):
    pass


class NoSQLStorage(MemoryStorage):
    pass


class FileStorage(MemoryStorage):
    pass


class CacheStorage(MemoryStorage):
    pass


@dataclass(frozen=True, slots=True)
class ConnectorRequest:
    location: str
    limit_bytes: int = 10_000_000


class Connector(Protocol):
    def read(self, request: ConnectorRequest) -> bytes: ...
    def write(self, request: ConnectorRequest, content: bytes) -> None: ...


class MemoryConnector:
    def __init__(self, values: dict[str, bytes] | None = None) -> None:
        self.values = dict(values or {})

    def read(self, request: ConnectorRequest) -> bytes:
        value = self.values[request.location]
        if len(value) > request.limit_bytes:
            raise ValueError("Import exceeds configured byte limit.")
        return value

    def write(self, request: ConnectorRequest, content: bytes) -> None:
        if len(content) > request.limit_bytes:
            raise ValueError("Export exceeds configured byte limit.")
        self.values[request.location] = bytes(content)


class S3Connector(MemoryConnector):
    pass


class AzureBlobConnector(MemoryConnector):
    pass


class GCSConnector(MemoryConnector):
    pass


class DatabaseConnector(MemoryConnector):
    pass


def validate_schema(schema: dict[str, Any], record: dict[str, Any]) -> tuple[str, ...]:
    fields = schema.get("fields", {})
    if not isinstance(fields, dict):
        raise ValueError("Schema fields must be a mapping.")
    return tuple(
        str(name)
        for name in schema.get("required", tuple(fields))
        if name not in record
    )


def compatible(
    previous: dict[str, Any], current: dict[str, Any], mode: str = "backward"
) -> bool:
    old, new = set(previous.get("fields", {})), set(current.get("fields", {}))
    if mode == "backward":
        return old <= new
    if mode == "forward":
        return new <= old
    if mode == "full":
        return old == new
    raise ValueError("Compatibility mode must be backward, forward, or full.")


def migrate(
    record: dict[str, Any],
    mapping: dict[str, str],
    defaults: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = {mapping.get(key, key): value for key, value in record.items()}
    for key, value in (defaults or {}).items():
        result.setdefault(key, value)
    return result


METRICS = (
    "datasets_total",
    "pipelines_total",
    "quality_failures_total",
    "imports_total",
    "exports_total",
)


class DataMetrics:
    def __init__(self) -> None:
        self.values: dict[str, float] = {name: 0 for name in METRICS}

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in self.values:
            raise ValueError("Unknown data metric.")
        self.values[name] += amount

    def snapshot(self) -> dict[str, float]:
        return dict(self.values)

    def render_prometheus(self) -> str:
        return "".join(f"{k} {v}\n" for k, v in self.values.items())


TRANSITIONS = {
    DatasetStatus.DRAFT: {DatasetStatus.IMPORTED, DatasetStatus.DELETED},
    DatasetStatus.IMPORTED: {DatasetStatus.VALIDATED, DatasetStatus.DELETED},
    DatasetStatus.VALIDATED: {DatasetStatus.PUBLISHED, DatasetStatus.ARCHIVED},
    DatasetStatus.PUBLISHED: {DatasetStatus.ARCHIVED},
    DatasetStatus.ARCHIVED: {DatasetStatus.DELETED},
    DatasetStatus.DELETED: set(),
}
SECTIONS = ("catalog", "datasets", "pipelines", "lineage", "quality", "classification")


class DataPlatform:
    def __init__(self) -> None:
        self.datasets: dict[str, Dataset] = {}
        self.pipelines: dict[str, Pipeline] = {}
        self.lineage: list[LineageEdge] = []
        self.quality_results: dict[str, QualityResult] = {}
        self.metrics = DataMetrics()

    @staticmethod
    def _authorize(tenant: str, workspace: str, scope: DataScope) -> None:
        if tenant != scope.tenant:
            raise PermissionError("Cross-tenant data access denied.")
        if workspace != scope.workspace:
            raise PermissionError("Cross-workspace data access denied.")

    def create_dataset(self, payload: dict[str, Any]) -> Dataset:
        item_id = str(payload["id"])
        if item_id in self.datasets:
            raise ValueError(f"Dataset already exists: {item_id}")
        item = Dataset(
            item_id,
            str(payload["name"]),
            str(payload.get("description", "")),
            str(payload["owner"]),
            str(payload["tenant"]),
            str(payload["workspace"]),
            Classification(str(payload.get("classification", "internal"))),
            str(payload.get("version", "1.0.0")),
            dict(payload.get("schema", {})),
            dict(payload.get("metadata", {})),
            tags=tuple(payload.get("tags", ())),
            domain=str(payload.get("domain", "")),
        )
        self.datasets[item.id] = item
        self.metrics.increment("datasets_total")
        return item

    def get_dataset(self, item_id: str, scope: DataScope) -> Dataset:
        item = self.datasets[item_id]
        self._authorize(item.tenant, item.workspace, scope)
        return item

    def list_datasets(
        self,
        scope: DataScope,
        query: str = "",
        tags: tuple[str, ...] = (),
        domains: tuple[str, ...] = (),
        owners: tuple[str, ...] = (),
        versions: tuple[str, ...] = (),
    ) -> tuple[Dataset, ...]:
        term = query.casefold()
        return tuple(
            i
            for i in self.datasets.values()
            if i.tenant == scope.tenant
            and i.workspace == scope.workspace
            and (not term or term in f"{i.name} {i.description}".casefold())
            and (not tags or set(tags) <= set(i.tags))
            and (not domains or i.domain in domains)
            and (not owners or i.owner in owners)
            and (not versions or i.version in versions)
        )

    def transition(self, item_id: str, status: str, scope: DataScope) -> Dataset:
        item = self.get_dataset(item_id, scope)
        target = DatasetStatus(status)
        if target not in TRANSITIONS[item.status]:
            raise ValueError(
                f"Invalid dataset transition: {item.status.value} -> {target.value}"
            )
        updated = replace(item, status=target)
        self.datasets[item_id] = updated
        return updated

    def create_pipeline(self, payload: dict[str, Any]) -> Pipeline:
        item_id = str(payload["id"])
        if item_id in self.pipelines:
            raise ValueError(f"Pipeline already exists: {item_id}")
        item = Pipeline(
            item_id,
            str(payload["name"]),
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload["source"]),
            str(payload["target"]),
            tuple(payload.get("transformations", ())),
            payload.get("schedule"),
            int(payload.get("max_retries", 3)),
        )
        self.pipelines[item.id] = item
        self.metrics.increment("pipelines_total")
        return item

    def run_pipeline(
        self, pipeline_id: str, scope: DataScope, operation: Callable[[], None]
    ) -> Pipeline:
        item = self.pipelines[pipeline_id]
        self._authorize(item.tenant, item.workspace, scope)
        item.status = PipelineStatus.RUNNING
        for attempt in range(1, item.max_retries + 2):
            item.attempts = attempt
            item.checkpoint = f"attempt:{attempt}"
            try:
                operation()
                item.status = PipelineStatus.SUCCEEDED
                return item
            except Exception:
                if attempt > item.max_retries:
                    item.status = PipelineStatus.FAILED
                    raise
        return item

    def import_data(
        self,
        dataset_id: str,
        scope: DataScope,
        connector: Connector,
        request: ConnectorRequest,
    ) -> bytes:
        self.get_dataset(dataset_id, scope)
        value = connector.read(request)
        self.metrics.increment("imports_total")
        return value

    def export_data(
        self,
        dataset_id: str,
        scope: DataScope,
        connector: Connector,
        request: ConnectorRequest,
        content: bytes,
    ) -> None:
        item = self.get_dataset(dataset_id, scope)
        if item.classification is Classification.RESTRICTED:
            raise PermissionError("Restricted datasets cannot be exported.")
        connector.write(request, content)
        self.metrics.increment("exports_total")

    def validate(
        self,
        dataset_id: str,
        scope: DataScope,
        records: tuple[dict[str, Any], ...],
        rules: tuple[QualityRule, ...] = (),
    ) -> QualityResult:
        item = self.get_dataset(dataset_id, scope)
        scores = {
            name: 1.0
            for name in (
                "completeness",
                "accuracy",
                "freshness",
                "consistency",
                "uniqueness",
            )
        }
        failures = []
        for rule in rules:
            if rule.dimension not in scores:
                raise ValueError(f"Unknown quality dimension: {rule.dimension}")
            score = 1.0
            if rule.dimension == "completeness" and rule.field:
                score = sum(row.get(rule.field) is not None for row in records) / max(
                    len(records), 1
                )
            elif rule.dimension == "uniqueness" and rule.field:
                counts = Counter(row.get(rule.field) for row in records)
                score = 1 - sum(value - 1 for value in counts.values()) / max(
                    len(records), 1
                )
            scores[rule.dimension] = min(scores[rule.dimension], score)
            if score < rule.threshold:
                failures.append(rule.name)
        if any(validate_schema(item.schema, row) for row in records):
            failures.append("schema-validation")
        result = QualityResult(dataset_id, scores, tuple(failures), not failures)
        self.quality_results[dataset_id] = result
        self.metrics.increment("quality_failures_total", len(failures))
        return result

    def record_lineage(self, edge: LineageEdge) -> None:
        if edge.source == edge.target:
            raise ValueError("Lineage source and target must differ.")
        if edge not in self.lineage:
            self.lineage.append(edge)

    def lineage_for(self, dataset_id: str) -> tuple[LineageEdge, ...]:
        return tuple(
            e
            for e in self.lineage
            if dataset_id in {e.source, e.target} or dataset_id in e.dependencies
        )

    def dashboard(self, scope: DataScope) -> dict[str, object]:
        return {
            "sections": SECTIONS,
            "datasets": len(self.list_datasets(scope)),
            "metrics": self.metrics.snapshot(),
        }


__all__ = (
    "AzureBlobConnector",
    "CacheStorage",
    "Classification",
    "ConnectorRequest",
    "DataMetrics",
    "DataPlatform",
    "DataScope",
    "DatabaseConnector",
    "Dataset",
    "DatasetStatus",
    "FileStorage",
    "GCSConnector",
    "LineageEdge",
    "MemoryConnector",
    "MemoryStorage",
    "NoSQLStorage",
    "ObjectStorage",
    "Pipeline",
    "PipelineStatus",
    "QualityResult",
    "QualityRule",
    "S3Connector",
    "SECTIONS",
    "SQLStorage",
    "compatible",
    "migrate",
    "validate_schema",
)
