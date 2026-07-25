/** Deterministic reference conversations used exclusively by tests, documentation, and UI contracts. */

import { createConversation } from "./store";
import type { Conversation } from "./models";

export const referenceConversation: Conversation = {
  ...createConversation("reference-chat", "Reference chat", "reference-session"),
  messages: [
    { id: "user-1", role: "user", content: "Summarize this reference workflow.", timestamp: "2026-01-01T00:00:00Z", status: "completed", metadata: {}, toolCalls: [], workflowId: "reference-workflow", executionId: null },
    { id: "assistant-1", role: "assistant", content: "The reference workflow completes deterministically.", timestamp: "2026-01-01T00:00:01Z", status: "completed", metadata: {}, toolCalls: [{ id: "tool-1", name: "reference_tool", status: "completed", summary: "Reference-only tool call." }], workflowId: "reference-workflow", executionId: "reference-execution" }
  ],
  memory: { sessionId: "reference-session", context: [] }
};
