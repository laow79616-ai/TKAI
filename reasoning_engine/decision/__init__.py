"""Rule, ranking, scoring, threshold, confidence, and fallback decisions."""

from __future__ import annotations

from typing import Any

from ..models import Decision


class DecisionEngine:
    def decide(
        self,
        options: list[dict[str, Any]],
        *,
        threshold: float = 0.5,
        fallback: str | None = None,
        rules: tuple[str, ...] = (),
    ) -> Decision:
        if not options:
            raise ValueError("At least one decision option is required.")
        if not 0 <= threshold <= 1:
            raise ValueError("Decision threshold must be between zero and one.")
        ranked = sorted(
            (
                (
                    str(item["option"]),
                    self._score(
                        dict(item.get("scores", {})),
                        float(item.get("score", 0)),
                    ),
                )
                for item in options
            ),
            key=lambda item: (-item[1], item[0]),
        )
        winner, score = ranked[0]
        selected = winner if score >= threshold else fallback
        if selected is None:
            raise ValueError(
                "No option met the threshold and no fallback was configured."
            )
        total = sum(max(value, 0) for _, value in ranked)
        confidence = score / total if total else 0
        return Decision(selected, score, confidence, fallback, tuple(ranked), rules)

    @staticmethod
    def _score(scores: dict[str, Any], default: float) -> float:
        values = [float(value) for value in scores.values()]
        score = sum(values) / len(values) if values else default
        return min(1.0, max(0.0, score))
