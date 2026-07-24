/** Serializable, frontend-only Agent Chat contracts. No Runtime objects are retained. */

export type ChatRole = "system" | "user" | "assistant" | "tool";
export type ChatStatus = "idle" | "typing" | "completed" | "failed" | "cancelled";
export type ChatValue = string | number | boolean | null | readonly ChatValue[] | { readonly [key: string]: ChatValue };

export interface ConversationMessage {
  readonly id: string;
  readonly role: ChatRole;
  readonly content: string;
  readonly timestamp: string;
  readonly status: ChatStatus;
  readonly metadata: Readonly<Record<string, ChatValue>>;
  readonly toolCalls: readonly ToolCall[];
  readonly workflowId: string | null;
  readonly executionId: string | null;
}

export interface ToolCall {
  readonly id: string;
  readonly name: string;
  readonly status: ChatStatus;
  readonly summary: string | null;
}

export interface ConversationMemory {
  readonly sessionId: string;
  readonly context: readonly ConversationMessage[];
}

export interface Conversation {
  readonly id: string;
  readonly title: string;
  readonly sessionId: string;
  readonly createdAt: string;
  readonly updatedAt: string;
  readonly messages: readonly ConversationMessage[];
  readonly memory: ConversationMemory;
}

export interface ChatSelection { readonly conversationId: string | null; readonly messageId: string | null; }
export interface AgentChatState { readonly conversations: readonly Conversation[]; readonly activeConversation: Conversation | null; readonly selection: ChatSelection; readonly status: ChatStatus; readonly error: string | null; readonly loading: boolean; }

export const initialAgentChatState: AgentChatState = { conversations: [], activeConversation: null, selection: { conversationId: null, messageId: null }, status: "idle", error: null, loading: false };
