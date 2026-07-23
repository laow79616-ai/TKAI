"""Stable JSON and Markdown renderers for offline benchmark results."""

from __future__ import annotations

import json

from .models import BenchmarkResult


class BenchmarkReport:
    """Render a named result using stable field order and fixed precision."""

    _FIELDS = (
        ("Operations", "operations", "d"),
        ("Elapsed", "elapsed_seconds", ".6f"),
        ("Ops/sec", "ops_per_second", ".2f"),
        ("Mean", "mean_latency_ms", ".6f"),
        ("P50", "p50_latency_ms", ".6f"),
        ("P95", "p95_latency_ms", ".6f"),
        ("P99", "p99_latency_ms", ".6f"),
        ("Min", "min_latency_ms", ".6f"),
        ("Max", "max_latency_ms", ".6f"),
    )

    @classmethod
    def to_markdown(cls, module: str, result: BenchmarkResult) -> str:
        """Return deterministic Markdown with every release-comparison field."""
        lines = ["| Module | Metric | Value |", "|---|---|---:|"]
        for label, attribute, pattern in cls._FIELDS:
            value = getattr(result, attribute)
            lines.append(f"| {module} | {label} | {value:{pattern}} |")
        return "\n".join(lines)

    @staticmethod
    def to_json(module: str, result: BenchmarkResult) -> str:
        """Return sorted JSON with a module label and primitive result values."""
        return json.dumps(
            {"module": module, "result": result.to_dict()},
            sort_keys=True,
            separators=(",", ":"),
        )
