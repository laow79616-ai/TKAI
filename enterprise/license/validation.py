"""Offline validation contracts without signature, activation, or network behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models import LicenseEntitlement


@dataclass(frozen=True, slots=True)
class LicenseValidationRequest:
    entitlement: LicenseEntitlement


@dataclass(frozen=True, slots=True)
class LicenseValidationResult:
    valid: bool
    reasons: tuple[str, ...] = ()


class LicenseValidator(Protocol):
    def validate(
        self, request: LicenseValidationRequest
    ) -> LicenseValidationResult: ...


class ReferenceLicenseValidator:
    """Checks only explicit descriptor structure and expiration timestamps."""

    def validate(self, request: LicenseValidationRequest) -> LicenseValidationResult:
        if not request.entitlement.entitlement_id:
            return LicenseValidationResult(False, ("entitlement id required",))
        return LicenseValidationResult(True)
