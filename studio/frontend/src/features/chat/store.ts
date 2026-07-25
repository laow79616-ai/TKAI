/** Pure conversation state transitions with explicit Agent SDK and REST dependencies. */

import type { StudioApiClient } from "../../api";
import { mapExecution } from "../executions/mapping";
import type { ExecutionSummary } from "../executions/models";
import type { AgentSDKAdapter } from "./agent";
import { type AgentChatState, type ChatStatus, type Conversation, type ConversationMessage, initialAgentChatState } from "./models";

const epoch = "1970-01-01T00:00:00.000Z";
const message = (id: string, role: ConversationMessage["role"], content: string, status: ChatStatus, extras: Partial<ConversationMessage> = {}): ConversationMessage => ({ id, role, content, timestamp: epoch, status, metadata: {}, toolCalls: [], workflowId: null, executionId: null, ...extras });
export const createConversation = (id: string, title: string, sessionId = id): Conversation => ({ id, title, sessionId, createdAt: epoch, updatedAt: epoch, messages: [], memory: { sessionId, context: [] } });
export const selectConversation = (state: AgentChatState, conversationId: string | null): AgentChatState => ({ ...state, activeConversation: conversationId === null ? null : state.conversations.find((item) => item.id === conversationId) ?? null, selection: { conversationId, messageId: null }, error: null });
export const selectMessage = (state: AgentChatState, messageId: string | null): AgentChatState => ({ ...state, selection: { ...state.selection, messageId } });
export const clear = (): AgentChatState => initialAgentChatState;
export const snapshot = (state: AgentChatState): string => JSON.stringify(state);
export const restore = (value: string): AgentChatState => { const parsed = JSON.parse(value) as Partial<AgentChatState>; if (!Array.isArray(parsed.conversations) || typeof parsed.loading !== "boolean") throw new Error("Invalid Agent Chat snapshot."); return { ...initialAgentChatState, ...parsed }; };
const replaceConversation = (state: AgentChatState, conversation: Conversation): AgentChatState => ({ ...state, conversations: state.conversations.some((item) => item.id === conversation.id) ? state.conversations.map((item) => item.id === conversation.id ? conversation : item) : [...state.conversations, conversation], activeConversation: conversation, selection: { ...state.selection, conversationId: conversation.id } });
export const appendMessage = (state: AgentChatState, conversation: Conversation, entry: ConversationMessage): AgentChatState => { const next = { ...conversation, messages: [...conversation.messages, entry], memory: { ...conversation.memory, context: [...conversation.memory.context, entry] }, updatedAt: epoch }; return replaceConversation(state, next); };
export async function sendMessage(adapter: AgentSDKAdapter, state: AgentChatState, input: string, messageId = "user-message", responseId = "assistant-message"): Promise<AgentChatState> {
  const conversation = state.activeConversation; if (conversation === null || !input.trim()) return { ...state, error: conversation === null ? "Select a conversation before sending a message." : "Message cannot be empty." };
  const pending = appendMessage({ ...state, status: "typing", error: null }, conversation, message(messageId, "user", input.trim(), "completed"));
  try { const response = await adapter.chat({ input: input.trim(), conversationId: conversation.id, sessionId: conversation.sessionId, memory: pending.activeConversation!.memory, metadata: {} }); const assistant = message(responseId, "assistant", response.output, "completed", { metadata: response.metadata, workflowId: response.workflowId, executionId: response.executionId, toolCalls: response.toolCalls.map((item) => ({ ...item, status: "completed" })) }); return { ...appendMessage(pending, pending.activeConversation!, assistant), status: "completed" }; } catch (error) { return { ...pending, status: "failed", error: "Agent chat request failed." }; }
}
/** Associate an existing frozen Execution REST record with the selected chat context. */
export async function loadConversationExecution(client: Pick<StudioApiClient, "execution">, executionId: string): Promise<ExecutionSummary | null> { try { const response = await client.execution(executionId); return response.success ? mapExecution(response.data, response.request_id) : null; } catch (error) { return null; } }
