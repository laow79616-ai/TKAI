"""Domain models for bounded, offline TikTok learning."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

SECRET_KEYS = frozenset(
    {"password", "secret", "token", "cookie", "session", "credential", "api_key"}
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def validate_confidence(value: float) -> None:
    if not 0 <= value <= 1:
        raise ValueError("Confidence must be within [0, 1].")


def validate_safe_mapping(value: dict[str, Any]) -> None:
    if SECRET_KEYS & {key.casefold() for key in value}:
        raise ValueError("Secrets are forbidden in learning records.")
    if len(str(value)) > 65_536:
        raise ValueError("Learning record exceeds the bounded size.")


class LearningStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class LearningContext:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:learning:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class LearningProfile:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    modules: tuple[str, ...]
    minimum_samples: int = 2
    status: LearningStatus = LearningStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not all((self.id, self.name, self.tenant, self.workspace, self.owner)):
            raise ValueError("Profile identity and ownership are required.")
        if not self.modules or self.minimum_samples < 2:
            raise ValueError("Profiles require modules and at least two samples.")
        validate_safe_mapping(self.metadata)


@dataclass(frozen=True, slots=True)
class HistoricalOutcome:
    source: str
    subject: str
    outcome: str
    score: float
    evidence_reference: str
    occurred_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        if not all((self.source, self.subject, self.outcome, self.evidence_reference)):
            raise ValueError("Historical outcomes require attributable evidence.")
        if not 0 <= self.score <= 1:
            raise ValueError("Outcome score must be within [0, 1].")


@dataclass(frozen=True, slots=True)
class LearningPattern:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    subject: str
    outcome: str
    sample_size: int
    average_score: float
    confidence: float
    evidence_references: tuple[str, ...]
    explanation: str
    created_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class Lesson:
    id: str
    pattern_id: str
    tenant: str
    workspace: str
    statement: str
    confidence: float
    evidence_references: tuple[str, ...]
    created_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class LearningRecommendation:
    id: str
    lesson_id: str
    tenant: str
    workspace: str
    title: str
    rationale: str
    confidence: float
    evidence_references: tuple[str, ...]
    advisory_only: bool = True
    requires_human_review: bool = True
    created_at: datetime = field(default_factory=utcnow)
