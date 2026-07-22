"""Small immutable options shared by routing strategies."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RoutingPolicy:
    """Declare passive eligibility rules without coupling to provider calls."""

    require_healthy: bool = True
    allow_half_open: bool = True
