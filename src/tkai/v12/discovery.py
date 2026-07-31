"""Allowlisted local metadata discovery without filesystem scanning."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .models import MetadataProfile


@dataclass(frozen=True)
class DiscoveryPolicy:
    source_allowlist: frozenset[str]
    maximum_sources: int = 16
    maximum_results: int = 100

    def __post_init__(self) -> None:
        if len(self.source_allowlist) > self.maximum_sources:
            raise ValueError("source allowlist exceeds bounded source count")
        if self.maximum_results < 1 or self.maximum_results > 1000:
            raise ValueError("maximum_results is outside safe bounds")


class LocalDiscovery:
    def __init__(self, policy: DiscoveryPolicy) -> None:
        self.policy = policy

    def discover(
        self,
        sources: dict[str, Iterable[MetadataProfile]],
        *,
        limit: int | None = None,
    ) -> tuple[MetadataProfile, ...]:
        limit = self.policy.maximum_results if limit is None else limit
        if limit < 0 or limit > self.policy.maximum_results:
            raise ValueError("result count exceeds discovery policy")
        if len(sources) > self.policy.maximum_sources:
            raise ValueError("source count exceeds discovery policy")
        rejected = set(sources) - self.policy.source_allowlist
        if rejected:
            raise ValueError(f"sources are not allowlisted: {sorted(rejected)}")
        items = [item for name in sorted(sources) for item in sources[name]]
        return tuple(sorted(items, key=lambda item: item.id))[:limit]
