"""Built-in provider identities for supported AI services."""

from __future__ import annotations

from .provider import BaseAIProvider


class OpenAIProvider(BaseAIProvider):
    """OpenAI-compatible provider identity."""

    name = "openai"
    default_model = "gpt-5.5"


class ClaudeProvider(BaseAIProvider):
    """Anthropic Claude provider identity."""

    name = "claude"
    default_model = "claude-sonnet"


class GeminiProvider(BaseAIProvider):
    """Google Gemini provider identity."""

    name = "gemini"
    default_model = "gemini-pro"


class DeepSeekProvider(BaseAIProvider):
    """DeepSeek provider identity."""

    name = "deepseek"
    default_model = "deepseek-chat"


class QwenProvider(BaseAIProvider):
    """Alibaba Qwen provider identity."""

    name = "qwen"
    default_model = "qwen-plus"


class OpenRouterProvider(BaseAIProvider):
    """OpenRouter provider identity."""

    name = "openrouter"
    default_model = "openai/gpt-5.5"
