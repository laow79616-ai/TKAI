"""Audit retention declarations that never archive or delete records."""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import AuditCategory


@dataclass(frozen=True, slots=True)
class AuditRetentionRule:
    retention_days: int | None = None
    archive_after_days: int | None = None
    delete_after_days: int | None = None
    legal_hold: bool = False


@dataclass(frozen=True, slots=True)
class AuditRetentionPolicy:
    default_rule: AuditRetentionRule = field(default_factory=AuditRetentionRule)
    category_overrides: tuple[tuple[AuditCategory, AuditRetentionRule], ...] = ()
    tenant_overrides: tuple[tuple[str, AuditRetentionRule], ...] = ()


@dataclass(frozen=True, slots=True)
class AuditRetentionDecision:
    rule: AuditRetentionRule
    reason: str
