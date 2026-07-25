"""Ensure Agent Chat remains a local, dependency-injected Studio product layer."""

from __future__ import annotations

from pathlib import Path


def _source(name: str) -> str:
    root = Path(__file__).resolve().parents[3] / "studio" / "frontend" / "src"
    return (root / "features" / "chat" / name).read_text(encoding="utf-8")


def test_conversation_message_session_and_memory_models_are_serializable() -> None:
    source = _source("models.ts")
    for token in (
        "Conversation",
        "ConversationMessage",
        "ConversationMemory",
        "AgentChatState",
        "ChatRole",
        "ChatStatus",
        "toolCalls",
        "workflowId",
        "executionId",
        '"typing"',
        '"failed"',
    ):
        assert token in source


def test_agent_sdk_bridge_is_explicit_and_never_references_runtime() -> None:
    source = _source("agent.ts")
    assert "AgentSDKAdapter" in source
    assert "chat(request" in source
    assert "tkai.sdk.Agent.chat" in source
    assert "Runtime" in source
    assert "fetch(" not in source
    assert "new Agent" not in source


def test_chat_store_uses_explicit_adapter_and_execution_client() -> None:
    source = _source("store.ts")
    for token in (
        "createConversation",
        "appendMessage",
        "sendMessage",
        "loadConversationExecution",
        "AgentSDKAdapter",
        'Pick<StudioApiClient, "execution">',
        "snapshot",
        "restore",
        "Select a conversation",
        "Message cannot be empty",
    ):
        assert token in source
    for forbidden in ("fetch(", "setInterval", "setTimeout", "new StudioApiClient"):
        assert forbidden not in source


def test_reference_conversation_covers_memory_tool_workflow_and_execution() -> None:
    source = _source("fixtures.ts")
    for token in (
        "referenceConversation",
        "reference-session",
        "reference_tool",
        "reference-workflow",
        "reference-execution",
    ):
        assert token in source


def test_chat_components_are_prop_driven_and_do_not_fetch() -> None:
    source = _source("components.tsx")
    for token in (
        "AgentChatPage",
        "ConversationSidebar",
        "ConversationHistory",
        "ChatMessage",
        "ChatInput",
        "TypingIndicator",
        "ChatStatusBadge",
        "ToolCallView",
        "WorkflowReference",
        "ExecutionReference",
        "ChatEmptyState",
        "ChatErrorState",
    ):
        assert token in source
    assert "fetch(" not in source
