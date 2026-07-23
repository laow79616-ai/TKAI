/** Serializable reference Workflow Designer model; it never executes a workflow. */

export type DesignerNodeKind = "task" | "condition" | "loop" | "retry" | "parallel" | "branch" | "end";
export interface DesignerNode { readonly id: string; readonly kind: DesignerNodeKind; readonly title: string; readonly position: readonly [number, number]; readonly inputs: readonly string[]; readonly outputs: readonly string[]; readonly metadata: Readonly<Record<string, unknown>>; readonly enabled: boolean; }
export interface DesignerEdge { readonly source: string; readonly target: string; readonly metadata: Readonly<Record<string, unknown>>; }
export interface ViewportState { readonly zoom: number; readonly pan: readonly [number, number]; readonly grid: boolean; }
export interface PropertyModel { readonly name: string; readonly description: string; readonly version: string; readonly tags: readonly string[]; }
export interface DesignerWorkflow { readonly workflowId: string; readonly projectId: string; readonly properties: PropertyModel; readonly nodes: readonly DesignerNode[]; readonly edges: readonly DesignerEdge[]; }
export interface DesignerStore { readonly workflow: DesignerWorkflow | null; readonly selection: readonly string[]; readonly validation: readonly ValidationIssue[]; readonly dirty: boolean; readonly viewport: ViewportState; }
export interface ValidationIssue { readonly code: "missing_start" | "missing_end" | "disconnected" | "invalid_edge" | "duplicate_node" | "duplicate_edge" | "empty"; readonly message: string; }

export const initialViewport: ViewportState = { zoom: 1, pan: [0, 0], grid: true };
export const initialDesignerStore: DesignerStore = { workflow: null, selection: [], validation: [], dirty: false, viewport: initialViewport };
export const setViewport = (store: DesignerStore, viewport: ViewportState): DesignerStore => ({ ...store, viewport });
export const select = (store: DesignerStore, ids: readonly string[]): DesignerStore => ({ ...store, selection: [...ids] });
export const connect = (workflow: DesignerWorkflow, edge: DesignerEdge): DesignerWorkflow => ({ ...workflow, edges: edge.source === edge.target || workflow.edges.some((item) => item.source === edge.source && item.target === edge.target) ? workflow.edges : [...workflow.edges, edge] });
export const disconnect = (workflow: DesignerWorkflow, edge: DesignerEdge): DesignerWorkflow => ({ ...workflow, edges: workflow.edges.filter((item) => item.source !== edge.source || item.target !== edge.target) });
export const snapshot = (store: DesignerStore): string => JSON.stringify(store);
export const restore = (value: string): DesignerStore => JSON.parse(value) as DesignerStore;
export const exportJson = (workflow: DesignerWorkflow): string => JSON.stringify(workflow, null, 2);
export const importJson = (value: string): DesignerWorkflow => JSON.parse(value) as DesignerWorkflow;
export const toWorkflowPayload = (workflow: DesignerWorkflow) => ({ workflow_id: workflow.workflowId, project_id: workflow.projectId, name: workflow.properties.name, nodes: workflow.nodes.map((node) => ({ node_id: node.id, kind: node.kind, label: node.title, position: node.position, configuration: node.metadata })), edges: workflow.edges.map((edge) => [edge.source, edge.target]), metadata: { description: workflow.properties.description, version: workflow.properties.version, tags: workflow.properties.tags } });

export function validate(workflow: DesignerWorkflow): readonly ValidationIssue[] {
  const issues: ValidationIssue[] = []; const ids = workflow.nodes.map((node) => node.id); const known = new Set(ids);
  if (workflow.nodes.length === 0) issues.push({ code: "empty", message: "Workflow has no nodes." });
  if (new Set(ids).size !== ids.length) issues.push({ code: "duplicate_node", message: "Node ids must be unique." });
  if (!workflow.nodes.some((node) => node.kind === "task")) issues.push({ code: "missing_start", message: "Workflow needs a task start node." });
  if (!workflow.nodes.some((node) => node.kind === "end")) issues.push({ code: "missing_end", message: "Workflow needs an end node." });
  const pairs = new Set<string>(); const connected = new Set<string>();
  for (const edge of workflow.edges) { const key = `${edge.source}:${edge.target}`; if (!known.has(edge.source) || !known.has(edge.target) || edge.source === edge.target) issues.push({ code: "invalid_edge", message: "Edge endpoints must be distinct declared nodes." }); if (pairs.has(key)) issues.push({ code: "duplicate_edge", message: "Edges must be unique." }); pairs.add(key); connected.add(edge.source); connected.add(edge.target); }
  if (workflow.nodes.some((node) => node.kind !== "end" && !connected.has(node.id))) issues.push({ code: "disconnected", message: "A non-end node is disconnected." });
  return issues;
}

export const referenceWorkflow: DesignerWorkflow = { workflowId: "reference-chat", projectId: "reference", properties: { name: "Simple Chat Flow", description: "Reference only", version: "1", tags: ["example"] }, nodes: [{ id: "task", kind: "task", title: "Task", position: [0, 0], inputs: [], outputs: ["result"], metadata: {}, enabled: true }, { id: "condition", kind: "condition", title: "Condition", position: [200, 0], inputs: ["result"], outputs: ["next"], metadata: {}, enabled: true }, { id: "end", kind: "end", title: "End", position: [400, 0], inputs: ["next"], outputs: [], metadata: {}, enabled: true }], edges: [{ source: "task", target: "condition", metadata: {} }, { source: "condition", target: "end", metadata: {} }] };
