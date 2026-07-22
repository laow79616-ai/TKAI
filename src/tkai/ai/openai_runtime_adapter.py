"""Runtime adapter for OpenAI-compatible request and response mapping."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from .errors import ProviderResponseError, ProviderTimeoutError
from .models import ChatRequest, ChatResponse, Usage
from .runtime import ProviderRuntime


class OpenAIProviderRuntimeAdapter:
    def __init__(
        self,
        runtime: ProviderRuntime,
        *,
        provider: str,
        model: str,
        headers: dict[str, str],
    ) -> None:
        self.runtime, self.provider, self.model, self.headers = (
            runtime,
            provider,
            model,
            headers,
        )

    def _response(
        self, data: dict[str, Any], model: str, *, streaming: bool = False
    ) -> ChatResponse:
        choice = data.get("choices", [{}])[0]
        message = choice.get("delta" if streaming else "message", {})
        usage = data.get("usage", {})
        return ChatResponse(
            message.get("content") or "",
            data.get("model", model),
            self.provider,
            choice.get("finish_reason"),
            Usage(total_tokens=int(usage.get("total_tokens", 0) or 0)),
            tuple(message.get("tool_calls", ())),
            data,
            data.get("id"),
        )

    async def chat(self, request: ChatRequest) -> ChatResponse:
        model = request.model or self.model
        payload = {
            "model": model,
            "messages": [
                {"role": m.role, "content": m.content} for m in request.messages
            ],
            **request.options,
        }
        try:
            async with self.runtime.request_scope() as transport:
                data = await transport.request(
                    "POST", "/chat/completions", json=payload, headers=self.headers
                )
        except TimeoutError as exc:
            raise ProviderTimeoutError("Provider request timed out") from exc
        except Exception as exc:
            raise ProviderResponseError("Provider request failed") from exc
        if not isinstance(data, dict):
            raise ProviderResponseError("Invalid provider response")
        return self._response(data, model)

    async def stream(self, request: ChatRequest) -> AsyncIterator[ChatResponse]:
        model = request.model or self.model
        try:
            async with self.runtime.request_scope() as transport:
                async for raw in transport.stream(
                    "POST", "/chat/completions", json={"model": model, "stream": True}
                ):
                    text = raw.decode().removeprefix("data: ").strip()
                    if text == "[DONE]":
                        return
                    try:
                        data = json.loads(text)
                    except json.JSONDecodeError as exc:
                        raise ProviderResponseError(
                            "Invalid streaming response"
                        ) from exc
                    yield self._response(data, model, streaming=True)
        except ProviderResponseError:
            raise
        except Exception as exc:
            raise ProviderResponseError("Provider streaming failed") from exc
