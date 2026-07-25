"""Static, offline checks for deterministic execution-monitor contracts."""

from __future__ import annotations

from pathlib import Path


def _source(name: str) -> str:
    root = Path(__file__).resolve().parents[3] / "studio" / "frontend" / "src"
    return (root / "features" / "executions" / name).read_text(encoding="utf-8")


def test_execution_monitor_models_cover_serializable_monitoring_domains() -> None:
    source = _source("models.ts")
    for token in (
        "ExecutionMonitorState",
        "ExecutionSummary",
        "ExecutionTimelineEvent",
        "ExecutionTreeNode",
        "ExecutionLogEntry",
        "ExecutionTrace",
        "ExecutionSpan",
        "ExecutionMetrics",
        "ExecutionSelection",
        "ExecutionFilter",
        '"queued"',
        '"running"',
        '"completed"',
        '"failed"',
        '"cancelled"',
        '"retrying"',
        "isTerminal",
    ):
        assert token in source


def test_mapping_keeps_rest_envelopes_stable_and_redacts_metadata() -> None:
    source = _source("mapping.ts")
    for token in (
        "mapExecution",
        "unwrapExecution",
        "unwrapExecutions",
        "parseStatus",
        "sortTimeline",
        "filterTimeline",
        "filterLogs",
        "buildTree",
        "wouldCycle",
        "sortSpans",
        "spanChildren",
        "computeMetrics",
        "redactMetadata",
        "authorization|api",
    ):
        assert token in source
    assert "fetch(" not in source


def test_store_requires_injected_client_and_has_no_background_polling() -> None:
    source = _source("store.ts")
    for token in (
        "loadExecutions",
        "selectExecution",
        "applyExecutionPayload",
        "setFilter",
        "selectTimelineEvent",
        "selectTreeNode",
        "snapshot",
        "restore",
        "Pick<StudioApiClient",
    ):
        assert token in source
    for forbidden in ("fetch(", "setInterval", "setTimeout", "new StudioApiClient"):
        assert forbidden not in source


def test_reference_executions_and_component_contracts_are_offline() -> None:
    fixtures = _source("fixtures.ts")
    components = _source("components.tsx")
    for token in (
        "completedTimeline",
        "failedRetryTimeline",
        "referenceTree",
        "referenceLogs",
        "failedSpan",
        "provider_started",
        "memory_access",
        "retry_scheduled",
    ):
        assert token in fixtures
    for component in (
        "ExecutionMonitorPage",
        "ExecutionList",
        "ExecutionSummaryCard",
        "ExecutionTimeline",
        "TimelineEvent",
        "ExecutionTree",
        "ExecutionTreeNode",
        "ExecutionLogs",
        "LogFilterBar",
        "TracePanel",
        "SpanList",
        "MetricsPanel",
        "ExecutionStatusBadge",
        "ExecutionErrorPanel",
        "ExecutionEmptyState",
        "ExecutionLoadingState",
    ):
        assert component in components
    assert "fetch(" not in components


def test_frozen_execution_client_endpoints_are_consumed_without_changes() -> None:
    root = Path(__file__).resolve().parents[3] / "studio" / "frontend" / "src"
    api = (root / "api.ts").read_text(encoding="utf-8")
    assert '"/executions"' in api
    assert "execution(executionId" in api
    assert "createExecution(workflowId" in api
