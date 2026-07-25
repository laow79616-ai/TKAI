import pytest

from tkai.ai import (
    AIClient,
    AIProviderError,
    ClaudeProvider,
    DeepSeekProvider,
    GeminiProvider,
    OpenAIProvider,
    OpenRouterProvider,
    QwenProvider,
)


def test_all_provider_identities_share_the_same_interface():
    providers = [
        OpenAIProvider(lambda request: f"openai:{request.prompt}"),
        ClaudeProvider(lambda request: f"claude:{request.prompt}"),
        GeminiProvider(lambda request: f"gemini:{request.prompt}"),
        DeepSeekProvider(lambda request: f"deepseek:{request.prompt}"),
        QwenProvider(lambda request: f"qwen:{request.prompt}"),
        OpenRouterProvider(lambda request: f"openrouter:{request.prompt}"),
    ]
    client = AIClient()
    for provider in providers:
        client.register(provider)

    response = client.generate("openai", "hello", temperature=0)

    assert client.registry.names() == [
        "claude",
        "deepseek",
        "gemini",
        "openai",
        "openrouter",
        "qwen",
    ]
    assert response.content == "openai:hello"
    assert response.provider == "openai"
    assert response.model == "gpt-5.5"


def test_provider_requires_an_explicit_transport_client():
    with pytest.raises(AIProviderError, match="completion client"):
        OpenAIProvider().generate("hello")
