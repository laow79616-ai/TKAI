"""Bounded ports for existing TKAI services; defaults are mock-only."""

from __future__ import annotations

from typing import Protocol


class ReferencePort(Protocol):
    def validate(self, reference: str, tenant: str, workspace: str) -> bool: ...


class ExecutionPort(Protocol):
    def execute(self, task: str, draft: str, tenant: str, workspace: str) -> bool: ...


class NullReferencePort:
    def validate(self, reference: str, tenant: str, workspace: str) -> bool:
        return bool(reference and tenant and workspace)


class NullExecutionPort:
    """Deterministic mock; it never contacts TikTok."""

    def execute(self, task: str, draft: str, tenant: str, workspace: str) -> bool:
        return bool(task and draft and tenant and workspace)
