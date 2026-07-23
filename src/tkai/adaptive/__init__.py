"""Optional, local adaptive routing based on bounded historical signals."""

from .doctor import AdaptiveDiagnostic, diagnose
from .errors import (
    AdaptiveRouterNotFoundError,
    AdaptiveRoutingError,
    NoAdaptiveProviderError,
)
from .history import ProviderHistory
from .manager import AdaptiveRoutingManager
from .models import ProviderScore, ProviderSignal, ProviderStatistics, RoutingDecision
from .policy_adapter import AdaptiveRoutingPolicyAdapter
from .registry import AdaptiveRouterRegistry
from .router import AdaptiveRouter
from .runtime_adapter import AdaptiveRoutingRuntimeAdapter
from .scoring import AdaptiveScoringEngine
from .weights import AdaptiveWeights

__all__ = (
    "AdaptiveDiagnostic",
    "AdaptiveRouter",
    "AdaptiveRouterNotFoundError",
    "AdaptiveRouterRegistry",
    "AdaptiveRoutingError",
    "AdaptiveRoutingManager",
    "AdaptiveRoutingPolicyAdapter",
    "AdaptiveRoutingRuntimeAdapter",
    "AdaptiveScoringEngine",
    "AdaptiveWeights",
    "NoAdaptiveProviderError",
    "ProviderHistory",
    "ProviderScore",
    "ProviderSignal",
    "ProviderStatistics",
    "RoutingDecision",
    "diagnose",
)
