"""Unified AI provider abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import replace
from typing import Any

from tkai.core.exceptions import AIProviderError

from .models import AIRequest, AIResponse

CompletionClient = Callable[[AIRequest], AIResponse | str]


class AIProvider(ABC):
    """Common interface implemented by every supported AI provider."""

    name: str
    default_model: str

    @abstractmethod
    def generate(
        self, prompt: str, *, model: str | None = None, **options: Any
    ) -> AIResponse:
        """Generate a response for ``prompt``."""


class BaseAIProvider(AIProvider):
    """Provider base class that delegates transport to an injected client."""

    name = "base"
    default_model = ""

    def __init__(self, client: CompletionClient | None = None) -> None:
        self.client = client

    def generate(
        self, prompt: str, *, model: str | None = None, **options: Any
    ) -> AIResponse:
        """Normalize the injected client's result into an :class:`AIResponse`."""
        if self.client is None:
            raise AIProviderError(
                f"Provider '{self.name}' requires a configured completion client"
            )
        selected_model = model or self.default_model
        request = AIRequest(prompt=prompt, model=selected_model, options=options)
        response = self.client(request)
        if isinstance(response, str):
            return AIResponse(response, self.name, selected_model, response)
        return replace(
            response,
            provider=self.name,
            model=response.model or selected_model,
        )
