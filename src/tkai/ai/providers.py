"""Built-in provider adapters with injected, offline-testable transports."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Iterator
from typing import Any

from .errors import ProviderConfigurationError, ProviderResponseError
from .models import (
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    ModelInfo,
    ProviderCapabilities,
    ProviderConfig,
    Usage,
)
from .openai_runtime_adapter import OpenAIProviderRuntimeAdapter
from .provider import BaseAIProvider, CompletionClient
from .runtime import OwnershipPolicy, ProviderRuntime
from .transport_adapter import resolve_transport

Transport = Callable[
    [str, dict[str, Any], dict[str, str]], dict[str, Any] | Iterator[dict[str, Any]]
]


class OpenAICompatibleProvider(BaseAIProvider):
    """OpenAI-shaped API adapter using an injectable request transport."""

    name = "openai-compatible"
    default_model = "gpt-5.5"
    capabilities = ProviderCapabilities(chat=True, streaming=True, embeddings=True)

    def __init__(
        self,
        client: CompletionClient | None = None,
        *,
        config: ProviderConfig | None = None,
        transport: Transport | None = None,
    ) -> None:
        super().__init__(client)
        self.config = config or ProviderConfig(name=self.name, type=self.name)
        self.transport = transport
        async_transport, owned = resolve_transport(
            transport, timeout=self.config.timeout
        )
        self._runtime = ProviderRuntime(
            async_transport,
            ownership=(
                OwnershipPolicy.RUNTIME_OWNED
                if owned
                else OwnershipPolicy.EXTERNALLY_OWNED
            ),
        )
        self._adapter = OpenAIProviderRuntimeAdapter(
            self._runtime,
            provider=self.name,
            model=self.config.model or self.default_model,
            headers=self._headers(),
        )

    async def achat(self, request: ChatRequest) -> ChatResponse:
        """Execute chat through the provider runtime adapter."""
        return await self._adapter.chat(request)

    async def astream_chat(self, request: ChatRequest) -> AsyncIterator[ChatResponse]:
        """Yield normalized runtime adapter streaming responses."""
        async for item in self._adapter.stream(request):
            yield item

    async def aclose(self) -> None:
        """Close the provider runtime according to ownership policy."""
        await self._runtime.close()

    def validate_config(self) -> None:
        """Validate injected transport or configured API credentials."""
        self.config.validate()
        if self.transport is None and self.client is None and not self.config.api_key:
            raise ProviderConfigurationError(
                f"Provider '{self.name}' requires an API key or injected transport"
            )

    def _headers(self) -> dict[str, str]:
        headers = dict(self.config.headers)
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        if self.config.organization:
            headers["OpenAI-Organization"] = self.config.organization
        if self.config.project:
            headers["OpenAI-Project"] = self.config.project
        return headers

    def _request(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self.transport is None:
            raise ProviderConfigurationError(
                f"Provider '{self.name}' requires an injected HTTP transport"
            )
        response = self.transport(path, payload, self._headers())
        if not isinstance(response, dict):
            raise ProviderResponseError(
                "Provider returned a streaming response unexpectedly"
            )
        return response

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Normalize an OpenAI-compatible chat-completions response."""
        model = request.model or self.config.model or self.default_model
        payload = {
            "model": model,
            "messages": [
                {
                    "role": item.role,
                    "content": item.content,
                    "tool_calls": list(item.tool_calls),
                }
                for item in request.messages
            ],
            **request.options,
        }
        data = self._request("/chat/completions", payload)
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        usage = data.get("usage", {})
        return ChatResponse(
            content=message.get("content") or "",
            model=data.get("model", model),
            provider=self.name,
            finish_reason=choice.get("finish_reason"),
            usage=Usage(
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            ),
            tool_calls=tuple(message.get("tool_calls", ())),
            raw_response=data,
            request_id=data.get("id"),
        )

    def stream_chat(self, request: ChatRequest) -> Iterator[ChatResponse]:
        """Normalize injected OpenAI-compatible streaming chunks."""
        if self.transport is None:
            raise ProviderConfigurationError("Streaming requires an injected transport")
        model = request.model or self.config.model or self.default_model
        response = self.transport(
            "/chat/completions",
            {
                "model": model,
                "stream": True,
                "messages": [
                    {"role": item.role, "content": item.content}
                    for item in request.messages
                ],
            },
            self._headers(),
        )
        if isinstance(response, dict):
            response = iter((response,))
        for chunk in response:
            choice = chunk.get("choices", [{}])[0]
            delta = choice.get("delta", {})
            usage = chunk.get("usage", {})
            yield ChatResponse(
                content=delta.get("content") or "",
                model=chunk.get("model", model),
                provider=self.name,
                finish_reason=choice.get("finish_reason"),
                usage=Usage(total_tokens=usage.get("total_tokens", 0)),
                tool_calls=tuple(delta.get("tool_calls", ())),
                raw_response=chunk,
                request_id=chunk.get("id"),
            )

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Normalize OpenAI-compatible embeddings."""
        model = request.model or self.config.model or self.default_model
        data = self._request(
            "/embeddings", {"model": model, "input": list(request.input)}
        )
        usage = data.get("usage", {})
        return EmbeddingResponse(
            embeddings=tuple(tuple(item["embedding"]) for item in data.get("data", [])),
            model=data.get("model", model),
            provider=self.name,
            usage=Usage(total_tokens=usage.get("total_tokens", 0)),
        )

    def list_models(self) -> list[ModelInfo]:
        """List models from an injected compatible endpoint when available."""
        if self.transport is None:
            return [
                ModelInfo(
                    self.config.model or self.default_model, self.name, True, True
                )
            ]
        data = self._request("/models", {})
        return [
            ModelInfo(item["id"], self.name, True, True)
            for item in data.get("data", [])
        ]


class OpenAIProvider(OpenAICompatibleProvider):
    """Official OpenAI identity over the compatible transport."""

    name = "openai"


class DeepSeekProvider(OpenAICompatibleProvider):
    """DeepSeek-compatible OpenAI endpoint identity."""

    name = "deepseek"
    default_model = "deepseek-chat"


class QwenProvider(OpenAICompatibleProvider):
    """Qwen-compatible OpenAI endpoint identity."""

    name = "qwen"
    default_model = "qwen-plus"


class OpenRouterProvider(OpenAICompatibleProvider):
    """OpenRouter adapter adding referer and application title headers."""

    name = "openrouter"
    default_model = "openai/gpt-5.5"

    def _headers(self) -> dict[str, str]:
        headers = super()._headers()
        if referer := self.config.headers.get("HTTP-Referer"):
            headers["HTTP-Referer"] = referer
        if title := self.config.headers.get("X-Title"):
            headers["X-Title"] = title
        return headers


class _OptionalSDKProvider(BaseAIProvider):
    """Adapter base that fails clearly until an optional SDK is installed."""

    dependency = ""

    def __init__(
        self, client: CompletionClient | None = None, *, sdk_client: Any = None
    ) -> None:
        super().__init__(client)
        self.sdk_client = sdk_client
        self._closed = False

    def validate_config(self) -> None:
        if self.client is not None or self.sdk_client is not None:
            return
        try:
            __import__(self.dependency)
        except ImportError as exc:
            raise ProviderConfigurationError(
                "Provider "
                f"'{self.name}' requires optional dependency '{self.dependency}'"
            ) from exc

    def _sdk_response(self, request: ChatRequest) -> Any:
        if self.sdk_client is None:
            self.validate_config()
            raise ProviderConfigurationError(
                f"Provider '{self.name}' has no SDK client"
            )
        if hasattr(self.sdk_client, "chat"):
            return self.sdk_client.chat(request)
        if hasattr(self.sdk_client, "messages") and hasattr(
            self.sdk_client.messages, "create"
        ):
            return self.sdk_client.messages.create(
                messages=request.messages, model=request.model
            )
        raise ProviderConfigurationError(
            f"Provider '{self.name}' SDK client has no chat method"
        )

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Normalize an injected SDK/fake response without exposing SDK types."""
        response = self._sdk_response(request)
        if isinstance(response, dict):
            content = response.get("content", "")
            usage = response.get("usage", {})
            model = response.get("model", request.model or self.default_model)
            finish = response.get("stop_reason") or response.get("finish_reason")
            tools = tuple(response.get("tool_calls") or response.get("tool_use") or ())
            request_id = response.get("id") or response.get("request_id")
        else:
            content = getattr(response, "content", "")
            usage = getattr(response, "usage", {})
            model = getattr(response, "model", request.model or self.default_model)
            finish = getattr(response, "stop_reason", None) or getattr(
                response, "finish_reason", None
            )
            tools = tuple(getattr(response, "tool_calls", ()) or ())
            request_id = getattr(response, "id", None)
        if isinstance(usage, dict):
            normalized_usage = Usage(
                int(usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0),
                int(usage.get("output_tokens", usage.get("completion_tokens", 0)) or 0),
                int(usage.get("total_tokens", 0) or 0),
            )
        else:
            normalized_usage = Usage()
        return ChatResponse(
            str(content),
            str(model),
            self.name,
            finish,
            normalized_usage,
            tools,
            response,
            request_id,
        )

    def stream_chat(self, request: ChatRequest) -> Iterator[ChatResponse]:
        """Normalize injected SDK stream chunks."""
        if self.sdk_client is None or not hasattr(self.sdk_client, "stream_chat"):
            raise ProviderConfigurationError(
                f"Provider '{self.name}' SDK client has no streaming method"
            )
        for chunk in self.sdk_client.stream_chat(request):
            if isinstance(chunk, dict):
                yield ChatResponse(
                    str(chunk.get("delta", chunk.get("content", "")) or ""),
                    chunk.get("model", request.model or self.default_model),
                    self.name,
                    chunk.get("finish_reason"),
                    raw_response=chunk,
                    request_id=chunk.get("id"),
                )
            else:
                yield ChatResponse(
                    str(chunk), request.model or self.default_model, self.name
                )

    def close(self) -> None:
        """Close an injected SDK client at most once."""
        if (
            not self._closed
            and self.sdk_client is not None
            and hasattr(self.sdk_client, "close")
        ):
            self.sdk_client.close()
        self._closed = True


class ClaudeProvider(_OptionalSDKProvider):
    """Anthropic adapter with lazy optional dependency validation."""

    name = "claude"
    default_model = "claude-sonnet"
    dependency = "anthropic"


class GeminiProvider(_OptionalSDKProvider):
    """Gemini adapter with lazy optional dependency validation."""

    name = "gemini"
    default_model = "gemini-pro"
    dependency = "google.generativeai"

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Normalize injected Gemini embedding results."""
        if self.sdk_client is None or not hasattr(self.sdk_client, "embed"):
            raise ProviderConfigurationError(
                "Gemini SDK client has no embedding method"
            )
        response = self.sdk_client.embed(list(request.input), model=request.model)
        values = (
            response.get("embeddings", response)
            if isinstance(response, dict)
            else response
        )
        return EmbeddingResponse(
            tuple(tuple(item) for item in values),
            request.model or self.default_model,
            self.name,
        )
