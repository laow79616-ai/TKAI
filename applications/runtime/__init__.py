"""Execution, quota, audit, and metrics."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from threading import RLock
from typing import Any
from uuid import uuid4

from applications.models import Deployment


@dataclass(frozen=True)
class AuditEvent:
    action: str
    actor: str
    resource_id: str
    details: dict[str, Any]


class ApplicationMetrics:
    NAMES = (
        "applications_total",
        "deployments_total",
        "application_runs_total",
        "application_failures_total",
    )

    def __init__(self) -> None:
        self._values: Counter[str] = Counter()
        self._lock = RLock()

    def increment(self, name: str, value: int = 1) -> None:
        if name not in self.NAMES:
            raise ValueError(f"Unknown metric: {name}")
        with self._lock:
            self._values[name] += value

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return {name: self._values[name] for name in self.NAMES}

    def render_prometheus(self) -> str:
        values = self.snapshot()
        return "".join(
            f"# TYPE {name} counter\n{name} {values[name]}\n" for name in self.NAMES
        )


class ApplicationRuntime:
    def __init__(self, metrics: ApplicationMetrics | None = None) -> None:
        self.metrics = metrics or ApplicationMetrics()
        self.audit: list[AuditEvent] = []

    def execute(
        self,
        deployment: Deployment,
        payload: dict[str, Any],
        actor: str,
        executor: Callable[[dict[str, Any]], Any] | None = None,
    ) -> dict[str, Any]:
        if deployment.runs >= deployment.quota:
            raise RuntimeError("Deployment quota exhausted.")
        run_id = str(uuid4())
        self.metrics.increment("application_runs_total")
        try:
            output = (
                executor(payload) if executor else {"accepted": True, "input": payload}
            )
        except Exception:
            self.metrics.increment("application_failures_total")
            self.audit.append(AuditEvent("run.failed", actor, run_id, {}))
            raise
        self.audit.append(AuditEvent("run.completed", actor, run_id, {}))
        return {"run_id": run_id, "status": "completed", "output": output}
