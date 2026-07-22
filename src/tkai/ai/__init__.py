"""Provider-neutral AI framework APIs."""

from tkai.core.exceptions import AIProviderError

from .client import AIClient
from .config import load_provider_config
from .errors import (
    AuthenticationError,
    CapabilityNotSupportedError,
    FallbackExhaustedError,
    ModelNotFoundError,
    NoCapableProviderError,
    ProviderConfigurationError,
    ProviderError,
    ProviderNotFoundError,
    ProviderResponseError,
    ProviderTimeoutError,
    RateLimitError,
)
from .fallback import FailureKind, FallbackCandidate, FallbackEngine, FallbackPolicy
from .manager import ProviderManager
from .models import (
    AIRequest,
    AIResponse,
    Capability,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    ModelInfo,
    ProviderCapabilities,
    ProviderConfig,
    Usage,
)
from .provider import AIProvider, BaseAIProvider, CompletionClient
from .providers import (
    ClaudeProvider,
    DeepSeekProvider,
    GeminiProvider,
    OpenAICompatibleProvider,
    OpenAIProvider,
    OpenRouterProvider,
    QwenProvider,
)
from .registry import ProviderRegistry
from .transport import HTTPResponse, raise_for_status

__all__ = (
    "AIClient",
    "AIProvider",
    "AIProviderError",
    "AIRequest",
    "AIResponse",
    "HTTPResponse",
    "AuthenticationError",
    "Capability",
    "CapabilityNotSupportedError",
    "BaseAIProvider",
    "ClaudeProvider",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "CompletionClient",
    "DeepSeekProvider",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "FallbackCandidate",
    "FallbackEngine",
    "FallbackExhaustedError",
    "FallbackPolicy",
    "FailureKind",
    "GeminiProvider",
    "OpenAIProvider",
    "OpenAICompatibleProvider",
    "OpenRouterProvider",
    "ProviderRegistry",
    "ProviderManager",
    "ProviderCapabilities",
    "ProviderConfig",
    "ProviderConfigurationError",
    "ProviderError",
    "ProviderNotFoundError",
    "ProviderResponseError",
    "ProviderTimeoutError",
    "QwenProvider",
    "RateLimitError",
    "ModelInfo",
    "ModelNotFoundError",
    "NoCapableProviderError",
    "Usage",
    "load_provider_config",
    "raise_for_status",
)
