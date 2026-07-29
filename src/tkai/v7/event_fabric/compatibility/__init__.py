"""Reference-only adapters for existing V6 event objects."""

from __future__ import annotations

from collections.abc import Mapping
from uuid import uuid4

from tkai.v7.contracts import Version

from ..contracts import EventModel


class V6EventAdapter:
    """Copies descriptive fields without changing or invoking V6 behavior."""

    def adapt(
        self,
        event: object,
        *,
        tenant_reference: str,
        workspace_reference: str,
        payload_reference: str,
    ) -> EventModel:
        metadata = getattr(event, "metadata", {})
        if not isinstance(metadata, Mapping):
            metadata = {}
        return EventModel(
            event_id=str(getattr(event, "event_id", uuid4())),
            event_type=str(getattr(event, "event_type", type(event).__name__)),
            event_version=Version.parse(str(getattr(event, "version", "6.0.0"))),
            source=str(getattr(event, "source", "v6.compatibility")),
            subject=str(getattr(event, "subject", "v6-event")),
            tenant_reference=tenant_reference,
            workspace_reference=workspace_reference,
            payload_reference=payload_reference,
            correlation_id=getattr(event, "correlation_id", None),
            causation_id=getattr(event, "causation_id", None),
            metadata=metadata,
        )


__all__ = ("V6EventAdapter",)
