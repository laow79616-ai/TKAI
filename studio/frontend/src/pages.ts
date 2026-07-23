/** Static Studio page declarations; rendering is intentionally deferred. */

export type StudioPage =
  | "dashboard"
  | "projects"
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
