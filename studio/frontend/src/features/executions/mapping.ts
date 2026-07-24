/** Deterministic mapping and view helpers for the frozen execution REST payload. */

import type { ApiError, ApiResponse, Execution } from "../../api";
import { type ExecutionFilter, type ExecutionLogEntry, type ExecutionMetrics, type ExecutionMonitorState, type ExecutionSpan, type ExecutionStatus, type ExecutionSummary, type ExecutionTimelineEvent, type ExecutionTrace, type ExecutionTreeNode, initialExecutionMonitorState } from "./models";

const statusMap: Readonly<Record<string, ExecutionStatus>> = { pending: "queued", queued: "queued", running: "running", succeeded: "completed", completed: "completed", failed: "failed", cancelled: "cancelled", retrying: "retrying" };
const forbidden = /authorization|api[_-]?key|credential|secret|token|password/i;
const safeTimestamp = (value: unknown): string | null => typeof value === "string" && !Number.isNaN(Date.parse(value)) ? value : null;
export const parseStatus = (value: unknown): ExecutionStatus => typeof value === "string" ? (statusMap[value.toLowerCase()] ?? "unknown") : "unknown";
export const statusLabel = (status: ExecutionStatus): string => status === "unknown" ? "Unavailable" : status.replace("_", " ");
export const redactMetadata = (value: unknown): Readonly<Record<string, string | number | boolean | null>> => {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  return Object.fromEntries(Object.entries(value as Record<string, unknown>).map(([key, item]) => [key, forbidden.test(key) ? "[redacted]" : typeof item === "string" || typeof item === "number" || typeof item === "boolean" || item === null ? item : "[unavailable]"]));
};
export const mapExecution = (execution: Execution, requestId: string | null = null): ExecutionSummary => ({ executionId: execution.execution_id, workflowId: execution.workflow_id, projectId: execution.project_id, status: parseStatus(execution.status), createdAt: safeTimestamp(execution.created_at), requestId, error: execution.error });
export const unwrapExecution = (response: ApiResponse<Execution>): { readonly summary: ExecutionSummary | null; readonly error: string | null; readonly requestId: string } => response.success ? { summary: mapExecution(response.data, response.request_id), error: null, requestId: response.request_id } : { summary: null, error: response.error.message, requestId: response.request_id };
export const unwrapExecutions = (response: ApiResponse<Execution[]>): { readonly summaries: readonly ExecutionSummary[]; readonly error: string | null; readonly requestId: string } => response.success ? { summaries: [...response.data].map((item) => mapExecution(item, response.request_id)).sort((left, right) => left.executionId.localeCompare(right.executionId)), error: null, requestId: response.request_id } : { summaries: [], error: response.error.message, requestId: response.request_id };
const timeKey = (value: string | null): number => value === null ? Number.MAX_SAFE_INTEGER : Date.parse(value);
export const sortTimeline = (items: readonly ExecutionTimelineEvent[]): readonly ExecutionTimelineEvent[] => [...items].sort((left, right) => timeKey(left.timestamp) - timeKey(right.timestamp) || left.sequence - right.sequence || left.id.localeCompare(right.id));
export const filterTimeline = (items: readonly ExecutionTimelineEvent[], filter: ExecutionFilter): readonly ExecutionTimelineEvent[] => sortTimeline(items.filter((item) => (filter.types.length === 0 || filter.types.includes(item.type)) && (filter.statuses.length === 0 || filter.statuses.includes(item.status)) && (filter.nodeId === null || item.nodeId === filter.nodeId) && (!filter.text || `${item.message ?? ""} ${item.type}`.toLowerCase().includes(filter.text.toLowerCase()))));
export const filterLogs = (items: readonly ExecutionLogEntry[], filter: ExecutionFilter): readonly ExecutionLogEntry[] => {
  const seen = new Set<string>();
  return [...items].sort((left, right) => timeKey(left.timestamp) - timeKey(right.timestamp) || left.id.localeCompare(right.id)).filter((item) => !seen.has(item.id) && (seen.add(item.id), true)).filter((item) => (filter.logLevels.length === 0 || filter.logLevels.includes(item.level)) && (filter.nodeId === null || item.nodeId === filter.nodeId) && (!filter.text || item.message.toLowerCase().includes(filter.text.toLowerCase())));
};
export function buildTree(nodes: readonly Omit<ExecutionTreeNode, "children">[]): ExecutionTreeNode | null {
  const entries = new Map<string, ExecutionTreeNode>(); const childIds = new Set<string>(); let root: ExecutionTreeNode | null = null;
  for (const item of nodes) { if (!item.id || entries.has(item.id)) continue; entries.set(item.id, { ...item, children: [] }); }
  for (const item of entries.values()) { if (item.parentId === null) { if (root === null) root = item; continue; } const parent = entries.get(item.parentId); if (parent && parent.id !== item.id && !wouldCycle(item.id, parent, entries)) { const descendants = parent.children as ExecutionTreeNode[]; descendants.push(item); childIds.add(item.id); } }
  if (root !== null) return root; return [...entries.values()].find((item) => !childIds.has(item.id)) ?? null;
}
const wouldCycle = (childId: string, parent: ExecutionTreeNode, nodes: ReadonlyMap<string, ExecutionTreeNode>): boolean => { let cursor: ExecutionTreeNode | undefined = parent; const seen = new Set<string>(); while (cursor && !seen.has(cursor.id)) { if (cursor.id === childId) return true; seen.add(cursor.id); cursor = cursor.parentId === null ? undefined : nodes.get(cursor.parentId); } return false; };
export const sortSpans = (spans: readonly ExecutionSpan[]): readonly ExecutionSpan[] => { const seen = new Set<string>(); return [...spans].filter((span) => !seen.has(span.spanId) && (seen.add(span.spanId), true)).sort((left, right) => timeKey(left.startedAt) - timeKey(right.startedAt) || left.spanId.localeCompare(right.spanId)); };
/** Build parent/child span relations defensively; orphan spans remain safe roots. */
export const spanChildren = (spans: readonly ExecutionSpan[]): ReadonlyMap<string | null, readonly ExecutionSpan[]> => {
  const known = new Set(spans.map((span) => span.spanId)); const groups = new Map<string | null, ExecutionSpan[]>();
  for (const span of sortSpans(spans)) { const parent = span.parentSpanId !== null && known.has(span.parentSpanId) ? span.parentSpanId : null; const children = groups.get(parent) ?? []; children.push(span); groups.set(parent, children); }
  return groups;
};
export const computeMetrics = (timeline: readonly ExecutionTimelineEvent[], logs: readonly ExecutionLogEntry[], tree: ExecutionTreeNode | null, trace: ExecutionTrace | null): ExecutionMetrics => { const count = (type: string) => timeline.filter((item) => item.type === type).length; const treeNodes = tree === null ? null : flattenTree(tree); return { totalDurationMs: trace?.durationMs ?? null, nodeCount: treeNodes?.filter((item) => item.kind === "node").length ?? null, completedNodeCount: treeNodes?.filter((item) => item.kind === "node" && item.status === "completed").length ?? null, failedNodeCount: treeNodes?.filter((item) => item.kind === "node" && item.status === "failed").length ?? null, retryCount: count("retry_scheduled") + count("retry_started"), toolCallCount: count("tool_started"), providerCallCount: count("provider_started"), memoryOperationCount: count("memory_access"), pluginCallCount: count("plugin_execution"), logCount: logs.length, errorCount: logs.filter((item) => item.level === "error" || item.level === "critical").length + count("execution_failed") + count("node_failed") }; };
const flattenTree = (node: ExecutionTreeNode): readonly ExecutionTreeNode[] => [node, ...node.children.flatMap(flattenTree)];
export const applyError = (state: ExecutionMonitorState, error: ApiError | string, requestId: string | null = null): ExecutionMonitorState => ({ ...state, loading: false, error: typeof error === "string" ? error : error.error.message, requestId });
export const applyPayload = (state: ExecutionMonitorState, summary: ExecutionSummary, requestId: string | null): ExecutionMonitorState => ({ ...state, activeExecution: summary, executions: state.executions.some((item) => item.executionId === summary.executionId) ? state.executions.map((item) => item.executionId === summary.executionId ? summary : item) : [...state.executions, summary].sort((left, right) => left.executionId.localeCompare(right.executionId)), loading: false, error: null, requestId, lastRefreshedAt: summary.createdAt });
export const emptyMonitor = (): ExecutionMonitorState => initialExecutionMonitorState;
