"""Prompt regression, benchmark, comparison, scoring, and usage evaluation."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from time import perf_counter

from studio.metrics import StudioMetrics


@dataclass(frozen=True, slots=True)
class EvaluationCase:
    case_id: str
    input: str
    expected: str | None = None


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    case_id: str
    output: str
    score: float
    latency_ms: float
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EvaluationRun:
    run_id: str
    name: str
    results: tuple[EvaluationResult, ...]

    @property
    def average_score(self) -> float:
        return (
            sum(item.score for item in self.results) / len(self.results)
            if self.results
            else 0.0
        )


class EvaluationStudio:
    """Run comparable evaluations through caller-supplied inference and scorers."""

    def __init__(
        self, id_factory: Callable[[str], str], metrics: StudioMetrics | None = None
    ) -> None:
        self._id_factory = id_factory
        self._metrics = metrics or StudioMetrics()
        self._runs: dict[str, EvaluationRun] = {}

    def run(
        self,
        name: str,
        cases: Sequence[EvaluationCase],
        invoke: Callable[[str], str],
        score: Callable[[EvaluationCase, str], float] | None = None,
    ) -> EvaluationRun:
        results: list[EvaluationResult] = []
        scorer = score or self._exact_match
        for case in cases:
            started = perf_counter()
            output = invoke(case.input)
            results.append(
                EvaluationResult(
                    case.case_id,
                    output,
                    scorer(case, output),
                    (perf_counter() - started) * 1000,
                    len(case.input.split()),
                    len(output.split()),
                )
            )
        run = EvaluationRun(self._id_factory("evaluation"), name, tuple(results))
        self._runs[run.run_id] = run
        self._metrics.increment("evaluation_runs")
        return run

    def compare(self, run_ids: Sequence[str]) -> tuple[EvaluationRun, ...]:
        return tuple(
            sorted(
                (self._runs[run_id] for run_id in run_ids),
                key=lambda item: (-item.average_score, item.run_id),
            )
        )

    def regression(
        self, baseline_id: str, candidate_id: str, tolerance: float = 0.0
    ) -> bool:
        return (
            self._runs[candidate_id].average_score + tolerance
            >= self._runs[baseline_id].average_score
        )

    @staticmethod
    def _exact_match(case: EvaluationCase, output: str) -> float:
        return float(case.expected is not None and case.expected == output)


__all__ = (
    "EvaluationCase",
    "EvaluationResult",
    "EvaluationRun",
    "EvaluationStudio",
)
