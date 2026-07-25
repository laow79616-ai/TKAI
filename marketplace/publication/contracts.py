"""Publication validator extension contracts without remote implementations."""

from __future__ import annotations

from typing import Protocol

from .models import (
    PublicationPolicy,
    PublicationPolicyResult,
    PublicationRequest,
    PublicationResult,
)


class PublicationValidator(Protocol):
    """Pure validation boundary with explicit request and policy inputs."""

    def validate(
        self, request: PublicationRequest, policy: PublicationPolicy
    ) -> PublicationResult: ...


class PublicationPolicyEvaluator(Protocol):
    """Pure policy-evaluation boundary without identity, trust, or network state."""

    def evaluate(
        self, request: PublicationRequest, policy: PublicationPolicy
    ) -> PublicationPolicyResult: ...


class PublicationDuplicateChecker(Protocol):
    """Explicit local duplicate-coordinate boundary without Registry access."""

    def exists(self, request: PublicationRequest) -> bool: ...
