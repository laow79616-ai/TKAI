"""Deterministic explicit region ranking with no network or automatic failover."""

from __future__ import annotations

from collections.abc import Sequence

from .errors import NoRegionAvailableError
from .models import Region, RegionDecision
from .policy import RegionPolicy
from .topology import RegionTopology


class MultiRegionRouter:
    """Rank provided regions by eligibility, role, priority, and local latency."""

    def __init__(
        self, topology: RegionTopology, policy: RegionPolicy | None = None
    ) -> None:
        self.topology = topology
        self.policy = policy or RegionPolicy()

    def rank(
        self,
        regions: Sequence[Region],
        *,
        fixed_region: str | None = None,
        required_capabilities: frozenset[str] = frozenset(),
    ) -> tuple[Region, ...]:
        """Return a stable ranking; breaker flags can be supplied as metadata."""
        candidates = [
            region
            for region in regions
            if region.enabled
            and self.topology.eligible(region)
            and self.policy.allows(region)
            and not bool(region.metadata.get("breaker_open", False))
            and required_capabilities.issubset(region.capabilities)
        ]
        if fixed_region is not None:
            candidates = [
                region for region in candidates if region.region_id == fixed_region
            ]
        preferred = {
            name: index for index, name in enumerate(self.policy.preferred_regions)
        }
        return tuple(
            sorted(
                candidates,
                key=lambda region: (
                    preferred.get(region.region_id, len(preferred)),
                    *self.topology.priority(region),
                    region.latency_estimate_ms,
                    region.region_id,
                ),
            )
        )

    def explain(
        self,
        regions: Sequence[Region],
        *,
        fixed_region: str | None = None,
        required_capabilities: frozenset[str] = frozenset(),
    ) -> RegionDecision:
        """Explain the first eligible region without applying it to any runtime."""
        ranked = self.rank(
            regions,
            fixed_region=fixed_region,
            required_capabilities=required_capabilities,
        )
        return RegionDecision(
            selected_region=ranked[0].region_id if ranked else None,
            candidates=tuple(region.region_id for region in ranked),
            reason=(
                "Selected deterministic eligible region"
                if ranked
                else "No eligible region"
            ),
        )

    def select(
        self,
        regions: Sequence[Region],
        *,
        fixed_region: str | None = None,
        required_capabilities: frozenset[str] = frozenset(),
    ) -> RegionDecision:
        """Select explicitly, or use first permitted fallback only when configured."""
        decision = self.explain(
            regions,
            fixed_region=fixed_region,
            required_capabilities=required_capabilities,
        )
        if decision.selected_region is not None:
            return decision
        if self.policy.allow_fallback:
            fallback = next((region for region in regions if region.enabled), None)
            if fallback is not None:
                return RegionDecision(
                    fallback.region_id,
                    (fallback.region_id,),
                    "No policy-eligible region; explicit fallback selected",
                    True,
                )
        raise NoRegionAvailableError("No multi-region candidate is available")
