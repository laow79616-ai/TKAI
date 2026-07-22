"""Provider-neutral AI framework APIs."""

from tkai.core.exceptions import AIProviderError

from .client import AIClient
from .errors import (
    AuthenticationError,
    ModelNotFoundError,
    ProviderConfigurationError,
    ProviderError,
    ProviderNotFoundError,
    ProviderResponseError,
    ProviderTimeoutError,
    RateLimitError,
)
from .manager import ProviderManager
from .models import (
    AIRequest,
    AIResponse,
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

__all__ = (
    "AIClient",
    "AIProvider",
    "AIProviderError",
    "AIRequest",
    "AIResponse",
    "AuthenticationError",
    "BaseAIProvider",
    "ClaudeProvider",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "CompletionClient",
    "DeepSeekProvider",
    "EmbeddingRequest",
    "EmbeddingResponse",
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
    "Usage",
)
