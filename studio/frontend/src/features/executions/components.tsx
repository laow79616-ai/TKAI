/** Presentation-only execution monitor component contracts; no fetch or Runtime access. */

import type { ExecutionFilter, ExecutionLogEntry, ExecutionMetrics, ExecutionMonitorState, ExecutionSpan, ExecutionSummary, ExecutionTimelineEvent, ExecutionTreeNode } from "./models";
export const ExecutionMonitorPage = ({ state }: { state: ExecutionMonitorState }) => <section>{state.activeExecution?.executionId ?? "No execution selected"}</section>;
export const ExecutionList = ({ executions }: { executions: readonly ExecutionSummary[] }) => <ul>{executions.map((item) => <li key={item.executionId}>{item.executionId}</li>)}</ul>;
export const ExecutionSummaryCard = ({ execution }: { execution: ExecutionSummary }) => <article>{execution.status}</article>;
export const ExecutionTimeline = ({ events }: { events: readonly ExecutionTimelineEvent[] }) => <ol>{events.map((item) => <TimelineEvent key={item.id} event={item} />)}</ol>;
export const TimelineEvent = ({ event }: { event: ExecutionTimelineEvent }) => <li>{event.message ?? event.type}</li>;
export const ExecutionTree = ({ node }: { node: ExecutionTreeNode | null }) => <section>{node?.label ?? "No execution tree"}</section>;
export const ExecutionTreeNode = ({ node }: { node: ExecutionTreeNode }) => <article>{node.label}</article>;
export const ExecutionLogs = ({ logs }: { logs: readonly ExecutionLogEntry[] }) => <ul>{logs.map((item) => <li key={item.id}>{item.message}</li>)}</ul>;
export const LogFilterBar = ({ filter }: { filter: ExecutionFilter }) => <span>{filter.text}</span>;
export const TracePanel = ({ spans }: { spans: readonly ExecutionSpan[] }) => <section>{spans.length} spans</section>;
export const SpanList = ({ spans }: { spans: readonly ExecutionSpan[] }) => <ul>{spans.map((item) => <li key={item.spanId}>{item.name}</li>)}</ul>;
export const MetricsPanel = ({ metrics }: { metrics: ExecutionMetrics | null }) => <section>{metrics?.totalDurationMs ?? "Unavailable"}</section>;
export const ExecutionStatusBadge = ({ status }: { status: string }) => <span>{status}</span>;
export const ExecutionErrorPanel = ({ error }: { error: string | null }) => error === null ? null : <aside>{error}</aside>;
export const ExecutionEmptyState = () => <section>No executions.</section>;
export const ExecutionLoadingState = () => <section>Loading executions.</section>;
