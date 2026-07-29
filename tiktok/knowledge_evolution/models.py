"""Domain models for explainable, read-only TikTok knowledge refinement."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

SECRET_KEYS = frozenset(
    {"password", "secret", "token", "cookie", "session", "credential", "api_key"}
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def validate_safe_mapping(value: dict[str, Any]) -> None:
    if SECRET_KEYS & {key.casefold() for key in value}:
        raise ValueError("Secrets are forbidden in knowledge records.")
    if len(str(value)) > 32_768:
        raise ValueError("Knowledge record exceeds the bounded size.")


def validate_confidence(value: float) -> None:
    if not 0 <= value <= 1:
        raise ValueError("Confidence must be within [0, 1].")


class RecommendationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class KnowledgeContext:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:knowledge:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class KnowledgeProfile:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    sources: tuple[str, ...]
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all((self.id, self.name, self.tenant, self.workspace, self.owner)):
            raise ValueError("Profile identity and ownership are required.")
        if not self.sources:
            raise ValueError("At least one bounded source is required.")
        validate_safe_mapping(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SourceEvidence:
    source: str
    reference: str
    summary: str
    confidence: float
    integrity_reference: str
    collected_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class KnowledgeVersion:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    number: int
    summary: str
    confidence: float
    evidence: tuple[SourceEvidence, ...]
    explanation: str
    previous_version_id: str | None = None
    created_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class KnowledgeComparison:
    id: str
    tenant: str
    workspace: str
    from_version_id: str
    to_version_id: str
    summary_changed: bool
    confidence_delta: float
    explanation: str
    created_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class KnowledgeRecommendation:
    id: str
    version_id: str
    tenant: str
    workspace: str
    title: str
    rationale: str
    confidence: float
    priority: RecommendationPriority
    evidence_references: tuple[str, ...]
    advisory_only: bool = True
    direct_execution: bool = False
    created_at: datetime = field(default_factory=utcnow)
