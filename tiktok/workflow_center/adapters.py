"""Ports that reuse existing TikTok centers without coupling their internals."""

from __future__ import annotations

from typing import Any, Protocol

from .models import WorkflowScope


class WorkflowNodePort(Protocol):
    def execute(
        self, action: str, payload: dict[str, Any], scope: WorkflowScope
    ) -> dict[str, Any]: ...

    def rollback(
        self, action: str, payload: dict[str, Any], scope: WorkflowScope
    ) -> None: ...


class NullWorkflowNodePort:
    """Safe mock/default port; production must inject approved center adapters."""

    def execute(
        self, action: str, payload: dict[str, Any], scope: WorkflowScope
    ) -> dict[str, Any]:
        return {
            "accepted": True,
            "action": action,
            "reference": payload.get("reference"),
        }

    def rollback(
        self, action: str, payload: dict[str, Any], scope: WorkflowScope
    ) -> None:
        return None
