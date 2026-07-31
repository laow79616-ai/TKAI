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
  | "logs"
  | "prompt-center"
  | "skill-center"
  | "agent-center"
  | "workflow-center"
  | "knowledge-center"
  | "model-center"
  | "memory-center"
  | "validation-center";

export const studioPages: readonly StudioPage[] = [
  "dashboard",
  "prompt-center",
  "skill-center",
  "agent-center",
  "workflow-center",
  "knowledge-center",
  "model-center",
  "memory-center",
  "validation-center",
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
