"""Offline tests for normalized provider adapters."""

from __future__ import annotations

from tkai.ai import (
    ChatMessage,
    ChatRequest,
    ClaudeProvider,
    EmbeddingRequest,
    GeminiProvider,
    OpenAIProvider,
    OpenRouterProvider,
    ProviderConfig,
    ProviderManager,
)


def test_openai_compatible_chat_stream_and_embeddings_are_normalized() -> None:
    def transport(path, payload, headers):
        assert headers["Authorization"] == "Bearer secret"
        if path == "/embeddings":
            return {"model": payload["model"], "data": [{"embedding": [1.0, 2.0]}]}
        if payload.get("stream"):
            return iter(
                (
                    {
                        "model": payload["model"],
                        "choices": [{"delta": {"content": "hi"}}],
                    },
                )
            )
        return {
            "id": "request-1",
            "model": payload["model"],
            "usage": {"total_tokens": 3},
            "choices": [{"message": {"content": "hello"}, "finish_reason": "stop"}],
        }

    provider = OpenAIProvider(
        config=ProviderConfig(name="openai", type="openai", api_key="secret"),
        transport=transport,
    )
    request = ChatRequest((ChatMessage("user", "hello"),), model="test")

    assert provider.chat(request).content == "hello"
    assert [item.content for item in provider.stream_chat(request)] == ["hi"]
    assert provider.embed(EmbeddingRequest(("hello",), "embed")).embeddings == (
        (1.0, 2.0),
    )


def test_openrouter_preserves_safe_custom_headers_and_manager_routes() -> None:
    captured = {}

    def transport(path, payload, headers):
        captured.update(headers)
        return {"model": payload["model"], "choices": [{"message": {"content": "ok"}}]}

    provider = OpenRouterProvider(
        config=ProviderConfig(
            name="openrouter",
            type="openrouter",
            api_key="secret",
            headers={"HTTP-Referer": "https://example.test", "X-Title": "TKAI"},
        ),
        transport=transport,
    )
    manager = ProviderManager()
    manager.register(provider, default=True)

    assert manager.chat(ChatRequest((ChatMessage("user", "hello"),))).content == "ok"
    assert captured["HTTP-Referer"] == "https://example.test"
    assert "secret" not in repr(provider.config)


def test_optional_sdk_adapters_support_injected_fakes_without_network() -> None:
    class Fake:
        def chat(self, request):
            return {
                "content": "fake",
                "model": request.model,
                "usage": {"input_tokens": 1},
            }

        def embed(self, values, model=None):
            return {"embeddings": [[float(index)] for index, _ in enumerate(values)]}

    request = ChatRequest(
        (ChatMessage("system", "rules"), ChatMessage("user", "hi")), "fake-model"
    )
    assert ClaudeProvider(sdk_client=Fake()).chat(request).content == "fake"
    assert GeminiProvider(sdk_client=Fake()).embed(
        EmbeddingRequest(("one", "two"))
    ).embeddings == ((0.0,), (1.0,))
