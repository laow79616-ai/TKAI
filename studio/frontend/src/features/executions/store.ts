/** Pure monitor-store transitions. Callers inject StudioApiClient explicitly. */

import type { StudioApiClient } from "../../api";
import { applyError, applyPayload, unwrapExecution, unwrapExecutions } from "./mapping";
import { type ExecutionFilter, type ExecutionMonitorState, initialExecutionMonitorState } from "./models";

export const selectExecution = (state: ExecutionMonitorState, executionId: string): ExecutionMonitorState => ({ ...state, activeExecution: state.executions.find((item) => item.executionId === executionId) ?? null, selection: { timelineEventId: null, treeNodeId: null } });
export const setFilter = (state: ExecutionMonitorState, filter: ExecutionFilter): ExecutionMonitorState => ({ ...state, filters: { ...filter, types: [...filter.types], statuses: [...filter.statuses], logLevels: [...filter.logLevels] } });
export const selectTimelineEvent = (state: ExecutionMonitorState, timelineEventId: string | null): ExecutionMonitorState => ({ ...state, selection: { ...state.selection, timelineEventId } });
export const selectTreeNode = (state: ExecutionMonitorState, treeNodeId: string | null): ExecutionMonitorState => ({ ...state, selection: { ...state.selection, treeNodeId } });
export const clear = (): ExecutionMonitorState => initialExecutionMonitorState;
export const snapshot = (state: ExecutionMonitorState): string => JSON.stringify(state);
export const restore = (value: string): ExecutionMonitorState => { const parsed = JSON.parse(value) as Partial<ExecutionMonitorState>; if (!Array.isArray(parsed.executions) || typeof parsed.loading !== "boolean") throw new Error("Invalid execution monitor snapshot."); return { ...initialExecutionMonitorState, ...parsed }; };
export async function loadExecutions(client: Pick<StudioApiClient, "executions">, state: ExecutionMonitorState): Promise<ExecutionMonitorState> { try { const mapped = unwrapExecutions(await client.executions()); return mapped.error ? applyError(state, mapped.error, mapped.requestId) : { ...state, executions: mapped.summaries, loading: false, error: null, requestId: mapped.requestId, lastRefreshedAt: new Date(0).toISOString() }; } catch (error) { return applyError(state, "Unable to load executions."); } }
export async function applyExecutionPayload(client: Pick<StudioApiClient, "execution">, state: ExecutionMonitorState, executionId: string): Promise<ExecutionMonitorState> { try { const mapped = unwrapExecution(await client.execution(executionId)); return mapped.summary === null ? applyError(state, mapped.error ?? "Unable to load execution.", mapped.requestId) : applyPayload(state, mapped.summary, mapped.requestId); } catch (error) { return applyError(state, "Unable to load execution."); } }
