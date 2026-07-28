/** Static Studio page declarations; rendering is intentionally deferred. */

export type StudioPage =
  | "dashboard"
  | "projects"
  | "prompt-studio"
  | "chat-studio"
  | "knowledge"
  | "knowledge-graph"
  | "rag"
  | "models"
  | "evaluation"
  | "workflow-studio"
  | "workflow"
  | "execution"
  | "agents"
  | "providers"
  | "memory"
  | "tools"
  | "plugins"
  | "settings"
  | "logs";

export const studioPages: readonly StudioPage[] = [
  "dashboard",
  "projects",
  "prompt-studio",
  "chat-studio",
  "knowledge",
  "knowledge-graph",
  "rag",
  "models",
  "evaluation",
  "workflow-studio",
  "workflow",
  "execution",
  "agents",
  "providers",
  "memory",
  "tools",
  "plugins",
  "settings",
  "logs"
];
