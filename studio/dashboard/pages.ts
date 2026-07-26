/** Stable Sprint-8 dashboard navigation contract. */
export const studioDashboardPages = [
  "Projects",
  "Prompt Studio",
  "Chat Studio",
  "Knowledge",
  "RAG",
  "Models",
  "Evaluation",
  "Workflow Studio",
] as const;

export type StudioDashboardPage = (typeof studioDashboardPages)[number];
