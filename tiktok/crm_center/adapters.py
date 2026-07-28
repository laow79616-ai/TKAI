"""Bounded reference interfaces to existing TikTok platform modules."""

from __future__ import annotations

from typing import Protocol

from .models import CRMScope


class ReferencePort(Protocol):
    def resolve(self, reference: str, scope: CRMScope) -> dict[str, str]: ...


class WorkflowHandoffPort(Protocol):
    def propose(self, reference: str, scope: CRMScope) -> str: ...


class BoundedTestDouble:
    def __init__(self) -> None:
        self.proposals: list[dict[str, str]] = []

    def resolve(self, reference: str, scope: CRMScope) -> dict[str, str]:
        return {
            "reference": reference,
            "tenant": scope.tenant,
            "workspace": scope.workspace,
        }

    def propose(self, reference: str, scope: CRMScope) -> str:
        self.proposals.append(
            {
                "reference": reference,
                "tenant": scope.tenant,
                "workspace": scope.workspace,
            }
        )
        return f"ref://crm-workflow/{len(self.proposals)}"
