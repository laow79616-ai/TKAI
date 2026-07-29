"""Domain models for the read-only TikTok Autonomous Intelligence Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

SECRET_KEYS = frozenset(
    {"password", "secret", "token", "cookie", "session", "credential"}
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def validate_safe_mapping(value: dict[str, Any]) -> None:
    if SECRET_KEYS & {key.casefold() for key in value}:
        raise ValueError("Secrets are forbidden in intelligence records.")
    if len(str(value)) > 32_768:
        raise ValueError("Intelligence record exceeds the bounded size.")


class IntelligenceStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class RecommendationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class IntelligenceContext:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:intelligence:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class IntelligenceProfile:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    modules: tuple[str, ...]
    status: IntelligenceStatus = IntelligenceStatus.DRAFT
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not all((self.id, self.name, self.tenant, self.workspace, self.owner)):
            raise ValueError("Profile identity and ownership are required.")
        if not self.modules or self.version < 1:
            raise ValueError("Profile modules and positive version are required.")
        validate_safe_mapping(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    module: str
    reference: str
    summary: str
    integrity_reference: str
    collected_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class ReasoningResult:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    question: str
    explanation: str
    evidence: tuple[EvidenceItem, ...]
    confidence: float
    assumptions: tuple[str, ...]
    created_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class Recommendation:
    id: str
    reasoning_id: str
    tenant: str
    workspace: str
    title: str
    rationale: str
    priority: RecommendationPriority
    confidence: float
    evidence_references: tuple[str, ...]
    advisory_only: bool = True
    requires_governance_approval: bool = True
    created_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class Prediction:
    id: str
    reasoning_id: str
    tenant: str
    workspace: str
    subject: str
    outcome: str
    horizon_seconds: int
    confidence: float
    assumptions: tuple[str, ...]
    evidence_references: tuple[str, ...]
    created_at: datetime = field(default_factory=utcnow)


def validate_confidence(value: float) -> None:
    if not 0 <= value <= 1:
        raise ValueError("Confidence must be within [0, 1].")
