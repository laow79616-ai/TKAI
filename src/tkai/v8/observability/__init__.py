"""In-memory, secret-filtered observability metadata for the Hyper Kernel."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock

from tkai.v8.security import filter_secrets


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class TraceHook:
    """A non-executing trace correlation hook."""

    name: str
    correlation_id: str
    metadata: Mapping[str, object]


class Observability:
    """Collects metrics, logs, traces, diagnostics, health, and audit metadata."""

    def __init__(self) -> None:
        self._metrics: Counter[str] = Counter()
        self._logs: list[dict[str, object]] = []
        self._traces: list[TraceHook] = []
        self._audit: list[dict[str, object]] = []
        self._lock = RLock()

    def increment(self, name: str, value: int = 1) -> None:
        with self._lock:
            self._metrics[name] += value

    def log(
        self, level: str, message: str, metadata: Mapping[str, object] | None = None
    ) -> None:
        with self._lock:
            self._logs.append(
                {
                    "timestamp": _now(),
                    "level": level,
                    "message": message,
                    "metadata": filter_secrets(metadata or {}),
                }
            )

    def trace(
        self,
        name: str,
        correlation_id: str,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        with self._lock:
            self._traces.append(
                TraceHook(
                    name,
                    correlation_id,
                    filter_secrets(metadata or {}),  # type: ignore[arg-type]
                )
            )

    def audit(
        self,
        action: str,
        actor: str,
        target: str,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        with self._lock:
            self._audit.append(
                {
                    "timestamp": _now(),
                    "action": action,
                    "actor": actor,
                    "target": target,
                    "metadata": filter_secrets(metadata or {}),
                }
            )
            self._metrics["audit_records"] += 1

    def metrics(self) -> dict[str, int]:
        return dict(sorted(self._metrics.items()))

    def logs(self) -> tuple[dict[str, object], ...]:
        return tuple(dict(item) for item in self._logs)

    def traces(self) -> tuple[TraceHook, ...]:
        return tuple(self._traces)

    def audit_records(self) -> tuple[dict[str, object], ...]:
        return tuple(dict(item) for item in self._audit)


__all__ = ("Observability", "TraceHook")
