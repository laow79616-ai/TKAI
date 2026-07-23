"""Explicit stage facade for the optional Policy Engine."""

from __future__ import annotations

from .engine import PolicyEngine
from .models import PolicyContext, PolicyExecution, PolicyStage


class PolicyPipeline:
    """Create explicit stage contexts and delegate their execution to one engine."""

    def __init__(self, engine: PolicyEngine) -> None:
        self.engine = engine

    def run(
        self, stage: PolicyStage, data: dict[str, object] | None = None
    ) -> tuple[PolicyContext, tuple[PolicyExecution, ...]]:
        """Run one declared stage; callers decide when and whether to invoke it."""
        context = PolicyContext(stage, {} if data is None else dict(data))
        return context, self.engine.execute(context)
