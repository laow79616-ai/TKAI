/** Deterministic reference data for monitor tests, examples, and component contracts. */

import type { ExecutionLogEntry, ExecutionSpan, ExecutionTimelineEvent, ExecutionTreeNode } from "./models";

export const completedTimeline: readonly ExecutionTimelineEvent[] = [
  { id: "created", type: "execution_created", status: "queued", timestamp: "2026-01-01T00:00:00Z", sequence: 0, nodeId: null, message: "Execution created", metadata: {} },
  { id: "provider", type: "provider_started", status: "running", timestamp: "2026-01-01T00:00:01Z", sequence: 1, nodeId: "task", message: "Reference provider started", metadata: {} },
  { id: "memory", type: "memory_access", status: "running", timestamp: "2026-01-01T00:00:02Z", sequence: 2, nodeId: "task", message: "Reference memory accessed", metadata: {} },
  { id: "done", type: "execution_completed", status: "completed", timestamp: "2026-01-01T00:00:03Z", sequence: 3, nodeId: null, message: "Execution completed", metadata: {} }
];
export const failedRetryTimeline: readonly ExecutionTimelineEvent[] = [
  { id: "failed", type: "node_failed", status: "failed", timestamp: "2026-01-02T00:00:00Z", sequence: 0, nodeId: "task", message: "Reference task failed", metadata: {} },
  { id: "retry", type: "retry_scheduled", status: "retrying", timestamp: "2026-01-02T00:00:01Z", sequence: 1, nodeId: "task", message: "Retry scheduled", metadata: {} },
  { id: "ended", type: "execution_failed", status: "failed", timestamp: "2026-01-02T00:00:02Z", sequence: 2, nodeId: null, message: "Execution failed", metadata: {} }
];
export const referenceTree: ExecutionTreeNode = { id: "execution", parentId: null, kind: "execution", label: "Reference execution", status: "completed", durationMs: 3000, error: null, retryCount: 0, children: [{ id: "workflow", parentId: "execution", kind: "workflow", label: "Reference workflow", status: "completed", durationMs: 3000, error: null, retryCount: 0, children: [{ id: "task", parentId: "workflow", kind: "node", label: "Task", status: "completed", durationMs: 2000, error: null, retryCount: 0, children: [] }]}] };
export const referenceLogs: readonly ExecutionLogEntry[] = [{ id: "log-1", timestamp: "2026-01-01T00:00:01Z", level: "info", message: "Reference provider completed", executionId: "reference-completed", workflowId: "reference-workflow", nodeId: "task", traceId: "trace-1", spanId: "span-1", metadata: { authorization: "[redacted]" } }];
export const failedSpan: ExecutionSpan = { spanId: "span-failed", parentSpanId: null, name: "Reference task", kind: "node", status: "failed", startedAt: "2026-01-02T00:00:00Z", endedAt: "2026-01-02T00:00:02Z", durationMs: 2000, attributes: {}, errorType: "ReferenceError" };
