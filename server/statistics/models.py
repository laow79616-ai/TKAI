"""Immutable, deterministic Marketplace Server Statistics domain models."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType


def _copy(values: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(sorted(values.items())))


class StatisticsSourceType(str, Enum):
    """Descriptive explicit Statistics source categories."""

    REGISTRY = "registry"
    PUBLISHER = "publisher"
    PACKAGE = "package"
    VERSION = "version"
    SEARCH = "search"
    RELEASE = "release"
    HEALTH = "health"
    CUSTOM = "custom"


class StatisticsMetricType(str, Enum):
    """Descriptive numeric metric types without an exporter or collector."""

    COUNTER = "counter"
    GAUGE = "gauge"
    DISTRIBUTION = "distribution"
    SUMMARY = "summary"


class StatisticsStatus(str, Enum):
    """Explicit source lifecycle states."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class StatisticsSort(str, Enum):
    """Stable Statistics record sorting keys."""

    RECORD_ID = "record_id"
    SOURCE_ID = "source_id"
    METRIC_NAME = "metric_name"
    VALUE = "value"
    SEQUENCE = "sequence"


class StatisticsGroupBy(str, Enum):
    """Explicit on-demand Statistics summary grouping keys."""

    SOURCE = "source"
    SOURCE_TYPE = "source_type"
    METRIC = "metric"
    DIMENSION = "dimension"


class StatisticsEventType(str, Enum):
    """Deterministic local Statistics lifecycle and recording events."""

    SOURCE_REGISTERED = "source_registered"
    SOURCE_UPDATED = "source_updated"
    SOURCE_ARCHIVED = "source_archived"
    SOURCE_RESTORED = "source_restored"
    RECORD_ADDED = "record_added"
    RECORDS_ADDED = "records_added"
    CLEARED = "cleared"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class StatisticsDimensions:
    """Immutable string dimensions used only for descriptive grouping."""

    values: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in self.values.items()
        ):
            raise ValueError("Statistics dimensions require string keys and values.")
        object.__setattr__(self, "values", _copy(self.values))

    def to_dict(self) -> dict[str, str]:
        """Return a stable defensive dimensions copy."""
        return dict(self.values)


NumericValue = int | float | tuple[int | float, ...]


@dataclass(frozen=True, slots=True)
class StatisticsValue:
    """Finite scalar or finite numeric tuple without implicit conversion."""

    value: NumericValue

    def __post_init__(self) -> None:
        values = self.value if isinstance(self.value, tuple) else (self.value,)
        if not values or any(not self._valid(item) for item in values):
            raise ValueError("Statistics values must be finite integers or floats.")
        object.__setattr__(
            self,
            "value",
            tuple(values) if isinstance(self.value, tuple) else self.value,
        )

    @staticmethod
    def _valid(value: object) -> bool:
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        )

    def scalar(self) -> int | float:
        """Return a scalar value or reject a descriptive distribution aggregation."""
        if isinstance(self.value, tuple):
            raise ValueError("Distribution values are not scalar.")
        return self.value

    def to_dict(self) -> int | float | list[int | float]:
        """Return a JSON-ready finite value."""
        return list(self.value) if isinstance(self.value, tuple) else self.value


@dataclass(frozen=True, slots=True)
class StatisticsMetric:
    """Explicit metric declaration without automatic collection semantics."""

    name: str
    metric_type: StatisticsMetricType
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Statistics metric name must not be empty.")

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "metric_type": self.metric_type.value,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class StatisticsSource:
    """Caller-provided Statistics source with no automatic domain discovery."""

    source_id: str
    source_type: StatisticsSourceType
    name: str
    description: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)
    status: StatisticsStatus = StatisticsStatus.ACTIVE

    def __post_init__(self) -> None:
        if not self.source_id or not self.name:
            raise ValueError("Statistics source id and name are required.")
        object.__setattr__(self, "metadata", _copy(self.metadata))

    def to_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type.value,
            "name": self.name,
            "description": self.description,
            "metadata": dict(self.metadata),
            "status": self.status.value,
        }


@dataclass(frozen=True, slots=True)
class StatisticsRecord:
    """Immutable caller-supplied numeric measurement with explicit sequence."""

    record_id: str
    source_id: str
    metric: StatisticsMetric
    value: StatisticsValue
    dimensions: StatisticsDimensions = field(default_factory=StatisticsDimensions)
    sequence: int = 0
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.record_id or not self.source_id or self.sequence < 0:
            raise ValueError(
                "Statistics record id, source id, and sequence are required."
            )
        object.__setattr__(self, "metadata", _copy(self.metadata))

    def to_dict(self) -> dict[str, object]:
        return {
            "record_id": self.record_id,
            "source_id": self.source_id,
            "metric": self.metric.to_dict(),
            "value": self.value.to_dict(),
            "dimensions": self.dimensions.to_dict(),
            "sequence": self.sequence,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class StatisticsFilter:
    """Explicit local Statistics record filters."""

    source_id: str | None = None
    source_type: StatisticsSourceType | None = None
    metric_name: str | None = None
    metric_type: StatisticsMetricType | None = None
    dimension_key: str | None = None
    dimension_value: str | None = None
    status: StatisticsStatus | None = None
    record_id: str | None = None


@dataclass(frozen=True, slots=True)
class StatisticsQuery:
    """Deterministic local record query with explicit bounded pagination."""

    statistics_filter: StatisticsFilter = field(default_factory=StatisticsFilter)
    sort: StatisticsSort = StatisticsSort.RECORD_ID
    descending: bool = False
    offset: int = 0
    limit: int = 50

    def __post_init__(self) -> None:
        if self.offset < 0 or self.limit <= 0:
            raise ValueError(
                "Statistics query offset must be non-negative and limit positive."
            )


@dataclass(frozen=True, slots=True)
class StatisticsResult:
    """Immutable deterministic page of Statistics records."""

    records: tuple[StatisticsRecord, ...] = ()
    total: int = 0
    query: StatisticsQuery = field(default_factory=StatisticsQuery)

    def __post_init__(self) -> None:
        object.__setattr__(self, "records", tuple(self.records))

    def to_dict(self) -> dict[str, object]:
        return {
            "records": [record.to_dict() for record in self.records],
            "total": self.total,
            "offset": self.query.offset,
            "limit": self.query.limit,
        }


@dataclass(frozen=True, slots=True)
class StatisticsSummary:
    """On-demand deterministic scalar summary with stable grouped totals."""

    matching_records: int = 0
    source_count: int = 0
    metric_count: int = 0
    total: int | float | None = None
    minimum: int | float | None = None
    maximum: int | float | None = None
    average: float | None = None
    grouped_values: Mapping[str, int | float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "grouped_values", _copy(self.grouped_values))

    def to_dict(self) -> dict[str, object]:
        return {
            "matching_records": self.matching_records,
            "source_count": self.source_count,
            "metric_count": self.metric_count,
            "total": self.total,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "average": self.average,
            "grouped_values": dict(self.grouped_values),
        }


@dataclass(frozen=True, slots=True)
class StatisticsCounters:
    """Fresh count-only source, record, and metric type counters."""

    total_sources: int = 0
    active_sources: int = 0
    archived_sources: int = 0
    total_records: int = 0
    metric_names: int = 0
    source_types: int = 0
    counters: int = 0
    gauges: int = 0
    distributions: int = 0
    summaries: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "total_sources": self.total_sources,
            "active_sources": self.active_sources,
            "archived_sources": self.archived_sources,
            "total_records": self.total_records,
            "metric_names": self.metric_names,
            "source_types": self.source_types,
            "counters": self.counters,
            "gauges": self.gauges,
            "distributions": self.distributions,
            "summaries": self.summaries,
        }


@dataclass(frozen=True, slots=True)
class StatisticsEvent:
    """Sequence-ordered local Statistics event without timestamp dependence."""

    sequence: int
    event_type: StatisticsEventType
    source_id: str | None = None
    record_id: str | None = None
    count: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "event_type": self.event_type.value,
            "source_id": self.source_id,
            "record_id": self.record_id,
            "count": self.count,
        }


@dataclass(frozen=True, slots=True)
class StatisticsSnapshot:
    """Stable immutable Statistics state with sources, records, events, and counters."""

    sources: tuple[StatisticsSource, ...] = ()
    records: tuple[StatisticsRecord, ...] = ()
    events: tuple[StatisticsEvent, ...] = ()
    counters: StatisticsCounters = field(default_factory=StatisticsCounters)
    closed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "sources", tuple(self.sources))
        object.__setattr__(self, "records", tuple(self.records))
        object.__setattr__(self, "events", tuple(self.events))

    def to_dict(self) -> dict[str, object]:
        return {
            "sources": [source.to_dict() for source in self.sources],
            "records": [record.to_dict() for record in self.records],
            "events": [event.to_dict() for event in self.events],
            "counters": self.counters.to_dict(),
            "closed": self.closed,
        }
