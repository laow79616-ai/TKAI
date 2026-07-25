import type { DesignerEdge, DesignerNode, DesignerStore } from "./workflow";
export const WorkflowCanvas = ({ store }: { store: DesignerStore }) => <section data-grid={store.viewport.grid}>Canvas</section>;
export const WorkflowNode = ({ node }: { node: DesignerNode }) => <article>{node.title}</article>;
export const WorkflowEdge = ({ edge }: { edge: DesignerEdge }) => <span>{edge.source} → {edge.target}</span>;
export const WorkflowToolbar = () => <nav>Zoom · Pan · Grid</nav>;
export const PropertyPanel = () => <aside>Properties</aside>;
export const ValidationPanel = () => <aside>Validation</aside>;
export const MiniMap = () => <aside>MiniMap</aside>;
