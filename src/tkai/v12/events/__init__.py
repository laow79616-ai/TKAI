"""V7-compatible, bounded local metadata event contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any

EVENT_TYPES = (
    "Platform Registered",
    "Agent Registered",
    "Agent Profile Validated",
    "Agent Relationship Registered",
    "Agent Dependency Issue Detected",
    "Memory Profile Registered",
    "Skill Registered",
    "Plugin Registered",
    "Workflow Registered",
    "Model Registered",
    "Knowledge Profile Registered",
    "Contract Registered",
    "Interface Registered",
    "Validation Failed",
    "Compatibility Gap Detected",
    "Integrity Gap Detected",
    "Trust Gap Detected",
    "Governance Issue Detected",
    "Security Issue Detected",
    "Health Degraded",
    "Review Required",
    "Approval Metadata Required",
    "Lifecycle Changed",
)


@dataclass(frozen=True)
class MetadataEvent:
    event_type: str
    subject_reference: str
    correlation_id: str
    occurred_at: datetime
    metadata: MappingProxyType[str, Any]

    @classmethod
    def create(
        cls, event_type: str, subject_reference: str, correlation_id: str
    ) -> MetadataEvent:
        if event_type not in EVENT_TYPES:
            raise ValueError("unsupported V12 event type")
        return cls(
            event_type,
            subject_reference,
            correlation_id,
            datetime.now(timezone.utc),
            MappingProxyType({}),
        )
