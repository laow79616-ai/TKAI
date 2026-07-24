/** Presentation-only Agent Chat component contracts; props are data, never fetch/Runtime. */

import type { AgentChatState, ChatStatus, Conversation, ConversationMessage, ToolCall } from "./models";
export const AgentChatPage = ({ state }: { state: AgentChatState }) => <section>{state.activeConversation?.title ?? "No conversation selected"}</section>;
export const ConversationSidebar = ({ conversations }: { conversations: readonly Conversation[] }) => <aside>{conversations.map((item) => <p key={item.id}>{item.title}</p>)}</aside>;
export const ConversationHistory = ({ conversation }: { conversation: Conversation | null }) => <section>{conversation?.messages.map((item) => <ChatMessage key={item.id} message={item} />)}</section>;
export const ChatMessage = ({ message }: { message: ConversationMessage }) => <article>{message.content}</article>;
export const ChatInput = ({ disabled }: { disabled: boolean }) => <input disabled={disabled} aria-label="Chat input" />;
export const TypingIndicator = ({ status }: { status: ChatStatus }) => status === "typing" ? <span>Agent is typing</span> : null;
export const ChatStatusBadge = ({ status }: { status: ChatStatus }) => <span>{status}</span>;
export const ToolCallView = ({ toolCall }: { toolCall: ToolCall }) => <aside>{toolCall.name}</aside>;
export const WorkflowReference = ({ workflowId }: { workflowId: string | null }) => <span>{workflowId ?? "No workflow"}</span>;
export const ExecutionReference = ({ executionId }: { executionId: string | null }) => <span>{executionId ?? "No execution"}</span>;
export const ChatEmptyState = () => <section>Start a reference conversation.</section>;
export const ChatErrorState = ({ error }: { error: string | null }) => error === null ? null : <aside>{error}</aside>;
