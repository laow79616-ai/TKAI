"""Bounded ports; production implementations delegate to existing TKAI systems."""

from __future__ import annotations

from typing import Any, Protocol

from .models import CandidateChange, RequestScope


class ReadOnlySignalPort(Protocol):
    def snapshot(self, module: str, scope: RequestScope) -> dict[str, Any]: ...


class ChangeApplicationPort(Protocol):
    def preconditions(
        self, candidate: CandidateChange, expected_version: int, scope: RequestScope
    ) -> bool: ...

    def apply(self, candidate: CandidateChange, scope: RequestScope) -> str: ...

    def rollback(
        self, candidate: CandidateChange, checkpoint: str, scope: RequestScope
    ) -> str: ...


class ReferenceIntegrityPort(Protocol):
    def validate_backup(self, reference: str, scope: RequestScope) -> bool: ...

    def validate_checkpoint(self, reference: str, scope: RequestScope) -> bool: ...


class BoundedTestDouble:
    """Offline adapter used by tests and local development; never accesses TikTok."""

    def __init__(self) -> None:
        self.applied: list[str] = []
        self.rolled_back: list[str] = []
        self.version = 1

    def snapshot(self, module: str, scope: RequestScope) -> dict[str, Any]:
        return {"module": module, "health": "healthy", "utilization": 0.75}

    def preconditions(
        self, candidate: CandidateChange, expected_version: int, scope: RequestScope
    ) -> bool:
        return expected_version == self.version

    def apply(self, candidate: CandidateChange, scope: RequestScope) -> str:
        self.applied.append(candidate.id)
        self.version += 1
        return f"bounded-change://{candidate.id}"

    def rollback(
        self, candidate: CandidateChange, checkpoint: str, scope: RequestScope
    ) -> str:
        self.rolled_back.append(candidate.id)
        return f"bounded-rollback://{candidate.id}"

    def validate_backup(self, reference: str, scope: RequestScope) -> bool:
        return reference.startswith("backup://")

    def validate_checkpoint(self, reference: str, scope: RequestScope) -> bool:
        return reference.startswith("checkpoint://")
