"""Thread-safe, passive circuit breaker foundation for provider integrations."""

from .breaker import CircuitBreaker
from .errors import CircuitBreakerError, CircuitBreakerNotFoundError
from .events import CircuitBreakerEvent
from .manager import CircuitBreakerManager
from .models import CircuitBreakerSnapshot, CircuitState
from .registry import CircuitBreakerRegistry
from .strategy import CircuitBreakerStrategy, ThresholdStrategy

__all__ = (
    "CircuitBreaker",
    "CircuitBreakerError",
    "CircuitBreakerEvent",
    "CircuitBreakerManager",
    "CircuitBreakerNotFoundError",
    "CircuitBreakerRegistry",
    "CircuitBreakerSnapshot",
    "CircuitBreakerStrategy",
    "CircuitState",
    "ThresholdStrategy",
)
