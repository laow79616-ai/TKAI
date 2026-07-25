"""Optional policy orchestration; it never changes existing manager defaults."""

from .engine import PolicyEngine
from .errors import PolicyError, PolicyNotFoundError, PolicyRegistrationError
from .events import PolicyEvent, PolicyExecuted, PolicyFailed, PolicySkipped
from .interfaces import (
    BreakerPolicyAdapter,
    CachePolicyAdapter,
    PluginPolicyAdapter,
    Policy,
    RateLimitPolicyAdapter,
    RoutingPolicyAdapter,
)
from .manager import PolicyManager
from .models import PolicyContext, PolicyDecision, PolicyExecution, PolicyStage
from .pipeline import PolicyPipeline
from .registry import PolicyRegistry

__all__ = (
    "BreakerPolicyAdapter",
    "CachePolicyAdapter",
    "PluginPolicyAdapter",
    "Policy",
    "PolicyContext",
    "PolicyDecision",
    "PolicyEngine",
    "PolicyError",
    "PolicyEvent",
    "PolicyExecuted",
    "PolicyExecution",
    "PolicyFailed",
    "PolicyManager",
    "PolicyNotFoundError",
    "PolicyPipeline",
    "PolicyRegistrationError",
    "PolicyRegistry",
    "PolicySkipped",
    "PolicyStage",
    "RateLimitPolicyAdapter",
    "RoutingPolicyAdapter",
)
