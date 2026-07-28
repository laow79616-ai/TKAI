"""Deterministic scenario simulation and comparison."""

from __future__ import annotations

from ..models import SimulationResult


class Simulator:
    def run(
        self,
        scenario: str,
        variables: dict[str, float],
        baselines: dict[str, float] | None = None,
        rollback_plan: tuple[str, ...] = (),
    ) -> SimulationResult:
        normalized = {key: float(value) for key, value in variables.items()}
        evaluation = (
            sum(normalized.values()) / len(normalized) if normalized else 0.0
        )
        comparison = {
            key: value - float((baselines or {}).get(key, 0))
            for key, value in normalized.items()
        }
        return SimulationResult(
            scenario=scenario,
            prediction={"variables": normalized, "outcome": evaluation},
            evaluation=evaluation,
            comparison=comparison,
            rollback_plan=rollback_plan,
        )
