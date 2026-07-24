"""Offline coverage for the Marketplace Server Statistics Foundation."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError

import pytest

from server.statistics import (
    ReferenceStatisticsService,
    ReferenceStatisticsStorage,
    StatisticsAggregationError,
    StatisticsClosedError,
    StatisticsConflictError,
    StatisticsDimensions,
    StatisticsEventType,
    StatisticsFilter,
    StatisticsGroupBy,
    StatisticsMetric,
    StatisticsMetricType,
    StatisticsQuery,
    StatisticsRecord,
    StatisticsSort,
    StatisticsSource,
    StatisticsSourceType,
    StatisticsStateError,
    StatisticsStatus,
    StatisticsValue,
)


def _source(
    identifier: str = "source-1",
    source_type: StatisticsSourceType = StatisticsSourceType.REGISTRY,
    metadata: dict[str, object] | None = None,
) -> StatisticsSource:
    return StatisticsSource(
        identifier,
        source_type,
        f"{identifier} source",
        metadata=metadata if metadata is not None else {"scope": "reference"},
    )


def _record(
    identifier: str,
    source_id: str = "source-1",
    value: int | float | tuple[int | float, ...] = 1,
    metric_name: str = "packages",
    metric_type: StatisticsMetricType = StatisticsMetricType.COUNTER,
    region: str = "east",
    sequence: int = 0,
) -> StatisticsRecord:
    return StatisticsRecord(
        identifier,
        source_id,
        StatisticsMetric(metric_name, metric_type),
        StatisticsValue(value),
        StatisticsDimensions({"region": region}),
        sequence,
        {"scope": "reference"},
    )


def test_models_are_immutable_defensive_json_safe_and_validate_values() -> None:
    metadata = {"scope": "reference"}
    source = _source(metadata=metadata)
    dimensions = StatisticsDimensions({"region": "east"})
    record = _record("record-1", value=(1, 2), region="east")

    metadata["scope"] = "changed"
    assert source.metadata["scope"] == "reference"
    assert dimensions.to_dict() == {"region": "east"}
    with pytest.raises(TypeError):
        source.metadata["new"] = "value"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        record.sequence = 4  # type: ignore[misc]
    for invalid in (True, float("nan"), float("inf"), "1"):
        with pytest.raises(ValueError):
            StatisticsValue(invalid)  # type: ignore[arg-type]
    assert json.loads(json.dumps(record.to_dict()))["value"] == [1, 2]


def test_source_lifecycle_is_idempotent_and_archived_sources_reject_records() -> None:
    service = ReferenceStatisticsService()
    service.register_source(_source())
    assert service.archive_source("source-1").status is StatisticsStatus.ARCHIVED
    assert service.archive_source("source-1").status is StatisticsStatus.ARCHIVED
    with pytest.raises(StatisticsStateError):
        service.record(_record("record-1"))
    assert service.restore_source("source-1").status is StatisticsStatus.ACTIVE
    assert service.restore_source("source-1").status is StatisticsStatus.ACTIVE
    assert service.record(_record("record-1")).record_id == "record-1"
    assert tuple(event.event_type for event in service.events()) == (
        StatisticsEventType.SOURCE_REGISTERED,
        StatisticsEventType.SOURCE_ARCHIVED,
        StatisticsEventType.SOURCE_RESTORED,
        StatisticsEventType.RECORD_ADDED,
    )


def test_record_many_is_atomic_and_conflicts_do_not_pollute_snapshots() -> None:
    service = ReferenceStatisticsService()
    service.register_source(_source())
    first = _record("record-1")
    duplicate = _record("record-1", sequence=1)
    with pytest.raises(StatisticsConflictError):
        service.record_many((first, duplicate))
    assert service.snapshot().records == ()
    service.record_many((first, _record("record-2", value=2, sequence=2)))
    with pytest.raises(StatisticsConflictError):
        service.record(_record("record-2"))
    assert tuple(record.record_id for record in service.list_records()) == (
        "record-1",
        "record-2",
    )


def test_query_filters_sorting_pagination_and_summary_are_deterministic() -> None:
    service = ReferenceStatisticsService()
    service.register_source(_source("a", StatisticsSourceType.REGISTRY))
    service.register_source(_source("b", StatisticsSourceType.PACKAGE))
    service.record_many(
        (
            _record("record-2", "b", 3, region="west", sequence=2),
            _record("record-1", "a", 2, region="east", sequence=1),
        )
    )
    result = service.query(
        StatisticsQuery(
            StatisticsFilter(source_type=StatisticsSourceType.PACKAGE),
            sort=StatisticsSort.VALUE,
        )
    )
    page = service.query(StatisticsQuery(sort=StatisticsSort.SEQUENCE, limit=1))
    summary = service.summarize(group_by=StatisticsGroupBy.SOURCE)
    dimension_summary = service.summarize(
        group_by=StatisticsGroupBy.DIMENSION, dimension_key="region"
    )

    assert result.records[0].record_id == "record-2"
    assert page.total == 2 and page.records[0].record_id == "record-1"
    assert (summary.total, summary.minimum, summary.maximum, summary.average) == (
        5,
        2,
        3,
        2.5,
    )
    assert summary.grouped_values == {"a": 2, "b": 3}
    assert dimension_summary.grouped_values == {"east": 2, "west": 3}


def test_aggregation_rejects_incompatible_metrics_and_distribution_values() -> None:
    service = ReferenceStatisticsService()
    service.register_source(_source())
    service.record(_record("scalar", value=1))
    service.record(_record("other", value=2, metric_name="versions"))
    with pytest.raises(StatisticsAggregationError):
        service.summarize()

    distributed = ReferenceStatisticsService()
    distributed.register_source(_source())
    distributed.record(
        _record(
            "distribution",
            value=(1, 2),
            metric_type=StatisticsMetricType.DISTRIBUTION,
        )
    )
    with pytest.raises(StatisticsAggregationError):
        distributed.summarize()
    assert ReferenceStatisticsService().summarize().matching_records == 0


def test_snapshot_counters_events_clear_and_close_retention() -> None:
    service = ReferenceStatisticsService()
    service.register_source(_source())
    service.record(_record("record-1"))
    service.clear()
    service.close()
    service.close()
    snapshot = service.snapshot()

    assert snapshot.sources == () and snapshot.records == ()
    assert snapshot.counters.total_records == 0
    assert snapshot.closed is True
    assert tuple(event.sequence for event in snapshot.events) == (1, 2, 3, 4)
    assert snapshot.events[-1].event_type is StatisticsEventType.CLOSED
    assert json.loads(json.dumps(snapshot.to_dict()))["closed"] is True
    with pytest.raises(StatisticsClosedError):
        service.list_sources()
    with pytest.raises(StatisticsClosedError):
        service.record(_record("after-close"))


def test_thread_safety_and_instance_isolation_are_bounded_and_deterministic() -> None:
    service = ReferenceStatisticsService(ReferenceStatisticsStorage())
    service.register_source(_source())

    def record(index: int) -> str:
        return service.record(_record(f"record-{index:02d}", sequence=index)).record_id

    with ThreadPoolExecutor(max_workers=8) as executor:
        identifiers = tuple(executor.map(record, range(32)))

    other = ReferenceStatisticsService()
    assert len(set(identifiers)) == 32
    assert service.counters().total_records == 32
    assert other.snapshot().records == ()
    assert tuple(event.sequence for event in service.events()) == tuple(range(1, 34))
