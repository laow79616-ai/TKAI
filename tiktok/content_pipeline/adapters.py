"""Bounded reference-only ports to existing TikTok modules."""

from __future__ import annotations

from typing import Protocol

from .models import ContentPackage, HandoffTarget, RequestScope, SafetyState


class ReferenceIntegrityPort(Protocol):
    def validate(self, reference: str, scope: RequestScope) -> bool: ...


class HandoffPort(Protocol):
    def handoff(
        self, target: HandoffTarget, package: ContentPackage, scope: RequestScope
    ) -> str: ...


class RiskStatePort(Protocol):
    def state(self, account_reference: str, scope: RequestScope) -> SafetyState: ...


class BoundedTestDouble:
    """Offline adapter recording reference handoffs; it never publishes."""

    def __init__(self) -> None:
        self.handoffs: list[tuple[HandoffTarget, str]] = []
        self.safety = SafetyState()

    def validate(self, reference: str, scope: RequestScope) -> bool:
        return bool(
            reference
            and "invalid" not in reference
            and scope.tenant
            and scope.workspace
        )

    def handoff(
        self, target: HandoffTarget, package: ContentPackage, scope: RequestScope
    ) -> str:
        self.handoffs.append((target, package.id))
        return f"ref://{target.value}/receipt/{package.id}"

    def state(self, account_reference: str, scope: RequestScope) -> SafetyState:
        return self.safety


class ExistingModuleHandoffAdapter:
    """Uses only bounded intake methods and cannot invoke publishing."""

    def __init__(self, modules: dict[HandoffTarget, object]) -> None:
        self.modules = modules

    def handoff(
        self, target: HandoffTarget, package: ContentPackage, scope: RequestScope
    ) -> str:
        intake = getattr(self.modules[target], "accept_content_handoff", None)
        if intake is None:
            raise RuntimeError(
                f"{target.value} does not expose bounded content intake."
            )
        receipt = intake(f"ref://content-package/{package.id}", scope)
        if not isinstance(receipt, str) or not receipt.startswith(
            ("ref://", "encrypted://")
        ):
            raise ValueError("Handoff adapter must return an opaque reference.")
        return receipt
