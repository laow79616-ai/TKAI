"""Bounded ports into the existing TikTok execution infrastructure."""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Protocol

from .models import ExecutionPlan, ExecutionScope, ExecutionStep, VerificationKind


class ExecutionInfrastructurePort(Protocol):
    def validate(
        self,
        kind: VerificationKind,
        plan: ExecutionPlan,
        scope: ExecutionScope,
    ) -> tuple[bool, str]: ...

    def dispatch(
        self,
        step: ExecutionStep,
        scope: ExecutionScope,
    ) -> dict[str, Any]: ...

    def checkpoint(
        self, execution_id: str, completed_steps: list[str], scope: ExecutionScope
    ) -> list[str]: ...

    def rollback(
        self, step: ExecutionStep, result_reference: str, scope: ExecutionScope
    ) -> None: ...

    def cleanup(self, execution_id: str, scope: ExecutionScope) -> None: ...


class ReferenceVaultPort(Protocol):
    def protect(self, value: str, scope: ExecutionScope) -> str: ...


class LocalReferenceVault:
    """Produces non-reversible local opaque references; never logs source values."""

    def __init__(self, key: bytes = b"tkai-local-execution-reference-v1") -> None:
        self._key = key

    def protect(self, value: str, scope: ExecutionScope) -> str:
        digest = sha256(
            self._key
            + scope.tenant.encode()
            + scope.workspace.encode()
            + value.encode()
        ).hexdigest()
        return f"sealed-ref://{digest}"


class LocalMockInfrastructure:
    """Offline-safe adapter used by local startup and tests."""

    def validate(
        self,
        kind: VerificationKind,
        plan: ExecutionPlan,
        scope: ExecutionScope,
    ) -> tuple[bool, str]:
        return True, f"{kind.value}:passed"

    def dispatch(self, step: ExecutionStep, scope: ExecutionScope) -> dict[str, Any]:
        return {
            "accepted": True,
            "reference": f"mock-result://{step.module}/{step.id}",
        }

    def checkpoint(
        self, execution_id: str, completed_steps: list[str], scope: ExecutionScope
    ) -> list[str]:
        return [f"mock-resource://{execution_id}/{item}" for item in completed_steps]

    def rollback(
        self, step: ExecutionStep, result_reference: str, scope: ExecutionScope
    ) -> None:
        return None

    def cleanup(self, execution_id: str, scope: ExecutionScope) -> None:
        return None
