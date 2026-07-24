"""Offline tests for the Enterprise Audit Foundation."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest

from enterprise.audit import (
    AuditActor,
    AuditActorKind,
    AuditCategory,
    AuditContext,
    AuditEvent,
    AuditIntegrityStatus,
    AuditIntegrityVerifier,
    AuditOutcome,
    AuditOutcomeStatus,
    AuditPage,
    AuditQuery,
    AuditRedactionPolicy,
    AuditRedactor,
    AuditRetentionPolicy,
    AuditRetentionRule,
    AuditSort,
    AuditTarget,
    AuditTargetKind,
    ReferenceAuditService,
)
from enterprise.audit.errors import AuditCapacityError, AuditClosedError


def event(
    event_id: str, sequence: int | None = None, secret: str | None = None
) -> AuditEvent:
    metadata = {"token": secret} if secret is not None else {}
    return AuditEvent(
        event_id,
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        "read",
        AuditCategory.TENANT,
        AuditActor("user-1", AuditActorKind.USER, "User"),
        AuditTarget("tenant-1", AuditTargetKind.TENANT, "Tenant"),
        AuditOutcome(AuditOutcomeStatus.SUCCESS),
        AuditContext("tenant-1", "org-1"),
        sequence,
        metadata,
    )


def test_context_event_serialization_actor_target_outcome_and_schema() -> None:
    item = event("event-1", 1)
    data = item.to_dict()
    assert data["schema_version"] == "1"
    assert data["timestamp"].endswith("+00:00")
    assert data["actor"]["kind"] == "user"
    assert data["target"]["kind"] == "tenant"


def test_reference_service_query_order_pagination_capacity_and_close() -> None:
    service = ReferenceAuditService(capacity=2, overflow="evict_oldest")
    service.record_many((event("event-1"), event("event-2"), event("event-3")))
    result = service.query(AuditQuery(page=AuditPage(0, 1), sort=AuditSort.DESCENDING))
    assert result.total == 2 and result.events[0].event_id == "event-3"
    assert service.get("event-2").event_id == "event-2"
    service.close()
    service.close()
    with pytest.raises(AuditClosedError):
        service.get("event-2")
    with pytest.raises(AuditCapacityError):
        rejected = ReferenceAuditService(capacity=1)
        rejected.record(event("a"))
        rejected.record(event("b"))


def test_redaction_retention_and_integrity_are_descriptive_only() -> None:
    item = event("event-1", 1, "secret-value")
    result = AuditRedactor().redact(item, AuditRedactionPolicy())
    assert "token" not in result.data["metadata"]
    assert (
        AuditRetentionPolicy(
            AuditRetentionRule(retention_days=30)
        ).default_rule.retention_days
        == 30
    )
    verifier = AuditIntegrityVerifier()
    assert verifier.verify_chain((item,)) is AuditIntegrityStatus.VERIFIED
    broken = AuditEvent(
        "event-2",
        item.timestamp,
        "read",
        AuditCategory.TENANT,
        item.actor,
        item.target,
        item.outcome,
        item.context,
        2,
        {"previous_digest": "bad"},
    )
    assert verifier.verify_chain((item, broken)) is AuditIntegrityStatus.BROKEN


def test_reference_service_is_thread_safe_and_snapshot_is_stable() -> None:
    service = ReferenceAuditService(capacity=16)
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(
            executor.map(
                lambda index: service.record(event(f"event-{index}")), range(8)
            )
        )
    assert len(service.snapshot()) == 8


def test_audit_documentation_declares_reference_only_scope() -> None:
    document = (
        __import__("pathlib").Path(__file__).parents[3] / "docs" / "Audit.md"
    ).read_text(encoding="utf-8")
    assert "no persistence" in document.lower()
    assert "not a compliance certification" in document.lower()
