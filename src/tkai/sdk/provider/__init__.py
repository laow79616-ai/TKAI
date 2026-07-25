"""TKAI 2.0 provider SDK contracts and offline reference implementation."""

from .capability import ProviderCapability
from .client import ProviderClient, ReferenceProvider
from .configuration import ProviderConfiguration
from .errors import (
    ProviderCapabilityError,
    ProviderConfigurationError,
    ProviderLifecycleError,
    ProviderNotFoundError,
    ProviderSDKError,
)
from .factory import ProviderFactory
from .hooks import LoggingHook, MetricsHook, ProviderHook, RetryHook, TelemetryHook
from .lifecycle import ProviderLifecycle
from .middleware import MiddlewarePipeline, ProviderMiddleware
from .registry import ProviderRegistry
from .request import ProviderRequest
from .response import ProviderResponse
from .streaming import (
    AsyncStreamingResponse,
    ReferenceStream,
    StreamChunk,
    StreamingResponse,
)
from .transport import ProviderTransport

__all__ = (
    "AsyncStreamingResponse",
    "LoggingHook",
    "MetricsHook",
    "MiddlewarePipeline",
    "ProviderCapability",
    "ProviderCapabilityError",
    "ProviderClient",
    "ProviderConfiguration",
    "ProviderConfigurationError",
    "ProviderFactory",
    "ProviderHook",
    "ProviderLifecycle",
    "ProviderLifecycleError",
    "ProviderMiddleware",
    "ProviderNotFoundError",
    "ProviderRegistry",
    "ProviderRequest",
    "ProviderResponse",
    "ProviderSDKError",
    "ProviderTransport",
    "ReferenceProvider",
    "ReferenceStream",
    "RetryHook",
    "StreamChunk",
    "StreamingResponse",
    "TelemetryHook",
)
