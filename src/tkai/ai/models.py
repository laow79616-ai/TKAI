"""Provider-neutral AI request and response models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


@dataclass(frozen=True, slots=True)
class AIRequest:
    """A text-generation request independent of a provider SDK."""

    prompt: str
    model: str | None = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AIResponse:
    """A normalized text-generation response."""

    content: str
    provider: str
    model: str
    raw: Any = None


@dataclass(frozen=True, slots=True)
class Usage:
    """Normalized provider token accounting."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass(frozen=True, slots=True)
class ModelInfo:
    """Provider-advertised model metadata."""

    id: str
    provider: str
    supports_chat: bool = True
    supports_embeddings: bool = False


class Capability(str, Enum):
    """Provider-neutral operations used for type-safe capability routing."""

    CHAT = "chat"
    STREAMING = "streaming"
    EMBEDDINGS = "embeddings"
    TOOLS = "tools"
    VISION = "vision"
    JSON_MODE = "json_mode"
    ASYNC = "async"


@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    """Immutable declaration of a provider or model's supported operations.

    A model-level declaration replaces its provider's default declaration. This
    allows a model to add, remove, or otherwise override capabilities without
    putting provider-specific conditions in routing code.
    """

    chat: bool = True
    streaming: bool = False
    embeddings: bool = False
    tools: bool = False
    vision: bool = False
    json_mode: bool = False
    async_: bool = False

    def supported(self) -> frozenset[Capability]:
        """Return the explicitly advertised capabilities as enum values."""
        values = {
            Capability.CHAT: self.chat,
            Capability.STREAMING: self.streaming,
            Capability.EMBEDDINGS: self.embeddings,
            Capability.TOOLS: self.tools,
            Capability.VISION: self.vision,
            Capability.JSON_MODE: self.json_mode,
            Capability.ASYNC: self.async_,
        }
        return frozenset(
            capability for capability, enabled in values.items() if enabled
        )

    def supports(self, required: frozenset[Capability]) -> bool:
        """Return whether every requested capability is explicitly supported."""
        return required.issubset(self.supported())

    def missing(self, required: frozenset[Capability]) -> frozenset[Capability]:
        """Return required capabilities absent from this declaration."""
        return required.difference(self.supported())


@dataclass(frozen=True, slots=True)
class ProviderConfig:
    """Configuration for a provider instance; secrets are never rendered."""

    name: str
    type: str
    api_key: str | None = field(default=None, repr=False)
    base_url: str | None = None
    model: str | None = None
    timeout: float = 60.0
    max_retries: int = 0
    organization: str | None = None
    project: str | None = None
    headers: dict[str, str] = field(default_factory=dict, repr=False)

    def validate(self) -> None:
        """Validate non-secret configuration constraints."""
        if not self.name or not self.type:
            raise ValueError("provider name and type are required")
        if self.timeout <= 0 or self.max_retries < 0:
            raise ValueError("timeout must be positive and max_retries non-negative")


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """Provider-neutral chat message, including tool-call metadata."""

    role: str
    content: str | None = None
    tool_calls: tuple[dict[str, Any], ...] = ()
    tool_call_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ChatRequest:
    """Normalized chat request."""

    messages: tuple[ChatMessage, ...]
    model: str | None = None
    stream: bool = False
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ChatResponse:
    """Normalized provider response, independent of SDK response objects."""

    content: str = ""
    model: str = ""
    provider: str = ""
    finish_reason: str | None = None
    usage: Usage = field(default_factory=Usage)
    tool_calls: tuple[dict[str, Any], ...] = ()
    raw_response: Any = field(default=None, repr=False)
    request_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EmbeddingRequest:
    """Normalized embedding request."""

    input: tuple[str, ...]
    model: str | None = None


@dataclass(frozen=True, slots=True)
class EmbeddingResponse:
    """Normalized embedding result."""

    embeddings: tuple[tuple[float, ...], ...]
    model: str
    provider: str
    usage: Usage = field(default_factory=Usage)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation."""
        return asdict(self)
