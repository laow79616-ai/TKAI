/** Explicit bridge contract for a host that invokes tkai.sdk.Agent.chat. */

import type { ChatValue, ConversationMemory } from "./models";

export interface AgentChatRequest { readonly input: string; readonly conversationId: string; readonly sessionId: string; readonly memory: ConversationMemory; readonly metadata: Readonly<Record<string, ChatValue>>; }
export interface AgentChatResponse { readonly output: string; readonly metadata: Readonly<Record<string, ChatValue>>; readonly workflowId: string | null; readonly executionId: string | null; readonly toolCalls: readonly { readonly id: string; readonly name: string; readonly summary: string | null }[]; }

/**
 * The Studio host injects this adapter. Its implementation may delegate to
 * `tkai.sdk.Agent.chat`; this frontend contract never imports or calls Runtime.
 */
export interface AgentSDKAdapter { chat(request: AgentChatRequest): Promise<AgentChatResponse>; }
