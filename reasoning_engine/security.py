"""Tenant/workspace isolation, RBAC, audit, and execution limits."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from .models import ReasoningScope, ReasoningSession


@dataclass(frozen=True, slots=True)
class ExecutionLimits:
    max_subtasks: int = 100
    max_depth: int = 20
    max_simulations: int = 50


class ReasoningSecurity:
    def __init__(self, limits: ExecutionLimits | None = None) -> None:
        self.limits = limits or ExecutionLimits()
        self._grants: dict[tuple[str, str, str], set[str]] = defaultdict(set)
        self.audit: list[dict[str, Any]] = []

    def grant(self, scope: ReasoningScope, permissions: set[str]) -> None:
        self._grants[(scope.tenant, scope.workspace, scope.actor)].update(permissions)

    def require(self, scope: ReasoningScope, permission: str) -> None:
        key = (scope.tenant, scope.workspace, scope.actor)
        if permission not in self._grants[key]:
            raise PermissionError(f"{permission} is required.")
        self.record(scope, permission)

    def isolate(self, scope: ReasoningScope, session: ReasoningSession) -> None:
        if session.tenant != scope.tenant:
            raise PermissionError("Cross-tenant reasoning access is denied.")
        if session.workspace != scope.workspace:
            raise PermissionError("Cross-workspace reasoning access is denied.")

    def enforce_plan(self, subtask_count: int, depth: int = 1) -> None:
        if subtask_count > self.limits.max_subtasks:
            raise ValueError("Reasoning plan exceeds the subtask execution limit.")
        if depth > self.limits.max_depth:
            raise ValueError("Reasoning plan exceeds the depth execution limit.")

    def enforce_simulations(self, count: int) -> None:
        if count > self.limits.max_simulations:
            raise ValueError("Simulation count exceeds the execution limit.")

    def record(self, scope: ReasoningScope, action: str, **details: Any) -> None:
        self.audit.append(
            {
                "tenant": scope.tenant,
                "workspace": scope.workspace,
                "actor": scope.actor,
                "action": action,
                **details,
            }
        )
