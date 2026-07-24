"""Deterministic hash descriptors; no signatures, keys, or tamper-proof storage."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum

from .models import AuditEvent


class AuditIntegrityStatus(str, Enum):
    VERIFIED = "verified"
    BROKEN = "broken"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class AuditIntegrityDescriptor:
    algorithm: str
    digest: str
    previous_digest: str | None
    sequence: int | None
    verified: bool
    reason: str | None = None


class AuditIntegrityVerifier:
    """Reference verifier over explicit event serialization only."""

    def describe(
        self, event: AuditEvent, previous_digest: str | None = None
    ) -> AuditIntegrityDescriptor:
        payload = json.dumps(
            event.to_dict(), sort_keys=True, separators=(",", ":"), default=str
        )
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return AuditIntegrityDescriptor(
            "sha256", digest, previous_digest, event.sequence, True
        )

    def verify_chain(self, events: tuple[AuditEvent, ...]) -> AuditIntegrityStatus:
        previous: str | None = None
        for event in events:
            descriptor = self.describe(event, previous)
            if event.metadata.get("previous_digest") not in (None, previous):
                return AuditIntegrityStatus.BROKEN
            previous = descriptor.digest
        return AuditIntegrityStatus.VERIFIED
