/** Frontend-only visual workflow contracts, mirroring no runtime implementation. */

export interface DesignerNode {
  readonly nodeId: string;
  readonly kind: string;
  readonly label: string;
  readonly position: readonly [number, number];
  readonly configuration: Readonly<Record<string, unknown>>;
}

export interface DesignerWorkflow {
  readonly workflowId: string;
  readonly projectId: string;
  readonly nodes: readonly DesignerNode[];
  readonly edges: readonly (readonly [string, string])[];
}
