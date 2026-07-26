"""Thread-safe Enterprise AI Studio metrics without exporter coupling."""

from __future__ import annotations

from collections import Counter
from threading import RLock

STUDIO_METRICS = (
    "studio_projects",
    "prompt_versions",
    "chat_sessions",
    "knowledge_documents",
    "rag_queries",
    "workflow_runs",
    "evaluation_runs",
)


class StudioMetrics:
    """Maintain the stable Sprint-8 metric contract for any exporter."""

    def __init__(self) -> None:
        self._values: Counter[str] = Counter({name: 0 for name in STUDIO_METRICS})
        self._lock = RLock()

    def increment(self, name: str, amount: int = 1) -> int:
        """Increment a declared counter and return its new value."""
        if name not in STUDIO_METRICS:
            raise ValueError(f"Unknown Studio metric: {name}")
        if amount < 0:
            raise ValueError("Studio counters cannot be decremented.")
        with self._lock:
            self._values[name] += amount
            return self._values[name]

    def snapshot(self) -> dict[str, int]:
        """Return a deterministic exporter-neutral metric snapshot."""
        with self._lock:
            return {name: self._values[name] for name in STUDIO_METRICS}
