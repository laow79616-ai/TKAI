"""Explicit candidate ranking and selection on top of adaptive scores."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from .errors import NoAdaptiveProviderError
from .models import ProviderScore, RoutingDecision
from .scoring import AdaptiveScoringEngine


class AdaptiveRouter:
    """Rank caller-provided candidates; never installs itself into legacy routing."""

    def __init__(
        self,
        scoring: AdaptiveScoringEngine,
        *,
        fallback: Callable[[Sequence[str]], str | None] | None = None,
    ) -> None:
        self.scoring = scoring
        self.fallback = fallback

    def rank(
        self,
        candidates: Sequence[str],
        context: Mapping[str, object] | None = None,
    ) -> tuple[ProviderScore, ...]:
        """Return deterministic high-score-first ranking with name tie breaking."""
        del context
        unique = sorted(set(candidates))
        scores = [self.scoring.score(provider) for provider in unique]
        return tuple(
            sorted(scores, key=lambda score: (-score.total_score, score.provider))
        )

    def explain(
        self,
        candidates: Sequence[str],
        context: Mapping[str, object] | None = None,
    ) -> RoutingDecision:
        """Return an explanation even when no candidate is eligible."""
        scores = self.rank(candidates, context)
        selected = next((score for score in scores if score.eligible), None)
        return RoutingDecision(
            selected_provider=selected.provider if selected else None,
            candidates=tuple(score.provider for score in scores),
            scores=scores,
            reason=(
                "Selected highest normalized adaptive score"
                if selected is not None
                else "No eligible adaptive provider"
            ),
            strategy=type(self).__name__,
        )

    def select(
        self,
        candidates: Sequence[str],
        context: Mapping[str, object] | None = None,
    ) -> RoutingDecision:
        """Select a provider or use the optional fixed fallback safely."""
        try:
            decision = self.explain(candidates, context)
        except Exception as error:
            fallback = self._fallback(candidates)
            if fallback is None:
                raise NoAdaptiveProviderError(
                    "Adaptive scoring failed and no fixed fallback is available"
                ) from error
            return RoutingDecision(
                selected_provider=fallback,
                candidates=tuple(sorted(set(candidates))),
                scores=(),
                reason="Adaptive scoring failed; fixed fallback selected",
                strategy=type(self).__name__,
                fallback_used=True,
            )
        if decision.selected_provider is not None:
            return decision
        fallback = self._fallback(candidates)
        if fallback is not None:
            return RoutingDecision(
                selected_provider=fallback,
                candidates=decision.candidates,
                scores=decision.scores,
                reason="Adaptive candidates unavailable; fixed fallback selected",
                strategy=type(self).__name__,
                fallback_used=True,
            )
        raise NoAdaptiveProviderError("No adaptive provider is eligible")

    def _fallback(self, candidates: Sequence[str]) -> str | None:
        """Invoke a caller-supplied legacy fallback without leaking its errors."""
        if self.fallback is None:
            return None
        try:
            fallback = self.fallback(tuple(candidates))
        except Exception:
            return None
        return fallback if fallback in candidates else None
