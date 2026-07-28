"""Bounded read-only source and reference-only handoff ports."""

from __future__ import annotations

from typing import Protocol

from .models import HandoffTarget, LeadScope


class SourcePort(Protocol):
    def read(self, reference: str, scope: LeadScope) -> dict[str, str]: ...


class HandoffPort(Protocol):
    def propose(
        self, target: HandoffTarget, reference: str, scope: LeadScope
    ) -> str: ...


class BoundedTestDouble:
    def __init__(self) -> None:
        self.proposals: list[dict[str, str]] = []

    def read(self, reference: str, scope: LeadScope) -> dict[str, str]:
        return {
            "reference": reference,
            "tenant": scope.tenant,
            "workspace": scope.workspace,
        }

    def propose(self, target: HandoffTarget, reference: str, scope: LeadScope) -> str:
        self.proposals.append(
            {
                "target": target.value,
                "reference": reference,
                "tenant": scope.tenant,
                "workspace": scope.workspace,
            }
        )
        return f"ref://lead-handoff/{target.value}/{len(self.proposals)}"
