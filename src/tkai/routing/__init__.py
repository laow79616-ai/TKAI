"""Provider-neutral, passive cost-aware routing foundation."""

from .errors import ProviderMetadataNotFoundError, RoutingError
from .events import RoutingEvent
from .manager import RoutingManager
from .models import ProviderMetadata, RoutingCandidate, RoutingDecision
from .policies import RoutingPolicy
from .registry import RoutingRegistry
from .router import ProviderRouter
from .strategy import CostAwareStrategy, RoutingStrategy

__all__ = (
    "CostAwareStrategy",
    "ProviderMetadata",
    "ProviderMetadataNotFoundError",
    "ProviderRouter",
    "RoutingCandidate",
    "RoutingDecision",
    "RoutingError",
    "RoutingEvent",
    "RoutingManager",
    "RoutingPolicy",
    "RoutingRegistry",
    "RoutingStrategy",
)
