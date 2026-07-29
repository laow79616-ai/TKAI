"""Immutable contracts for the V7 unified AI metadata plane."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def frozen_map(value: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


def _required(value: str, name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{name} is required")


class ProviderKind(str, Enum):
    LOCAL = "local"
    OPENAI_COMPATIBLE = "openai-compatible"
    GENERIC_HTTP = "generic-http"
    MOCK = "mock"
    TEST = "test"


class Lifecycle(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_REVIEW = "requires-review"


class RiskClass(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PROHIBITED = "prohibited"


@dataclass(frozen=True, slots=True)
class Scope:
    tenant_id: str
    workspace_id: str
    namespace: str = "ai"

    def __post_init__(self) -> None:
        _required(self.tenant_id, "tenant_id")
        _required(self.workspace_id, "workspace_id")


@dataclass(frozen=True, slots=True)
class Health:
    status: str = "unknown"
    checks: Mapping[str, str] = field(default_factory=frozen_map)
    observed_at: datetime = field(default_factory=now_utc)

    def __post_init__(self) -> None:
        object.__setattr__(self, "checks", frozen_map(self.checks))


@dataclass(frozen=True, slots=True)
class ProviderDefinition:
    provider_id: str
    kind: ProviderKind
    scope: Scope
    display_name: str
    endpoint_reference: str | None = None
    secret_references: tuple[str, ...] = ()
    isolation_metadata: Mapping[str, Any] = field(default_factory=frozen_map)
    metadata: Mapping[str, Any] = field(default_factory=frozen_map)
    health: Health = field(default_factory=Health)
    enabled: bool = True

    def __post_init__(self) -> None:
        _required(self.provider_id, "provider_id")
        if any(not ref.startswith("secret://") for ref in self.secret_references):
            raise ValueError("credentials must be secret:// references only")
        for name in ("isolation_metadata", "metadata"):
            object.__setattr__(self, name, frozen_map(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class ContextLimits:
    input_tokens: int
    output_tokens: int

    def __post_init__(self) -> None:
        if self.input_tokens <= 0 or self.output_tokens <= 0:
            raise ValueError("context limits must be positive")


@dataclass(frozen=True, slots=True)
class AIModel:
    model_id: str
    provider_id: str
    model_name: str
    version: str
    scope: Scope
    capabilities: frozenset[str]
    context_limits: ContextLimits
    supported_modalities: frozenset[str] = frozenset({"text"})
    prompt_template_references: tuple[str, ...] = ()
    safety_policy_references: tuple[str, ...] = ()
    evaluation_references: tuple[str, ...] = ()
    lifecycle: Lifecycle = Lifecycle.DRAFT
    metadata: Mapping[str, Any] = field(default_factory=frozen_map)
    health: Health = field(default_factory=Health)
    metrics: Mapping[str, float] = field(default_factory=frozen_map)
    audit: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for value, name in (
            (self.model_id, "model_id"),
            (self.provider_id, "provider_id"),
            (self.model_name, "model_name"),
            (self.version, "version"),
        ):
            _required(value, name)
        for name in ("metadata", "metrics"):
            object.__setattr__(self, name, frozen_map(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    template_id: str
    version: str
    scope: Scope
    template: str
    variables: tuple[str, ...] = ()
    constraints: Mapping[str, Any] = field(default_factory=frozen_map)
    compatibility: Mapping[str, str] = field(default_factory=frozen_map)
    metadata: Mapping[str, Any] = field(default_factory=frozen_map)
    history: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _required(self.template_id, "template_id")
        _required(self.version, "version")
        if len(set(self.variables)) != len(self.variables):
            raise ValueError("template variables must be unique")
        for name in ("constraints", "compatibility", "metadata"):
            object.__setattr__(self, name, frozen_map(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class ReasoningSession:
    session_id: str
    scope: Scope
    model_id: str
    context_reference: str | None = None
    evidence_references: tuple[str, ...] = ()
    confidence: float | None = None
    evaluation_reference: str | None = None
    trace_reference: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=frozen_map)

    def __post_init__(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if {"chain_of_thought", "hidden_reasoning", "reasoning_content"}.intersection(
            self.metadata
        ):
            raise ValueError(
                "hidden reasoning and chain-of-thought storage are prohibited"
            )
        object.__setattr__(self, "metadata", frozen_map(self.metadata))


@dataclass(frozen=True, slots=True)
class Evaluation:
    evaluation_id: str
    scope: Scope
    model_id: str
    quality_score: float
    latency_ms: float
    compatibility_score: float
    safety_score: float
    regression_references: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=frozen_map)

    def __post_init__(self) -> None:
        for name in ("quality_score", "compatibility_score", "safety_score"):
            if not 0 <= getattr(self, name) <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.latency_ms < 0:
            raise ValueError("latency_ms cannot be negative")
        object.__setattr__(self, "metadata", frozen_map(self.metadata))


@dataclass(frozen=True, slots=True)
class GovernanceRecord:
    governance_id: str
    scope: Scope
    subject_reference: str
    approval_status: ReviewStatus = ReviewStatus.PENDING
    policy_references: tuple[str, ...] = ()
    safety_references: tuple[str, ...] = ()
    compliance_references: tuple[str, ...] = ()
    audit_references: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=frozen_map)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", frozen_map(self.metadata))


@dataclass(frozen=True, slots=True)
class SafetyPolicy:
    policy_id: str
    scope: Scope
    content_policy_references: tuple[str, ...]
    risk_classification: RiskClass
    review_status: ReviewStatus
    metadata: Mapping[str, Any] = field(default_factory=frozen_map)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", frozen_map(self.metadata))


@dataclass(frozen=True, slots=True)
class RouteRequest:
    scope: Scope
    required_capabilities: frozenset[str]
    compatible_versions: frozenset[str] = frozenset()
    required_modalities: frozenset[str] = frozenset({"text"})


@dataclass(frozen=True, slots=True)
class RouteDecision:
    model_id: str | None
    candidate_model_ids: tuple[str, ...]
    fallback_model_ids: tuple[str, ...]
    reason: str
    executable: bool = False


REDACTED_KEYS = frozenset(
    {"api_key", "authorization", "credential", "password", "secret", "token"}
)


def serialize(value: Any) -> Any:
    if is_dataclass(value):
        return {
            item.name: serialize(getattr(value, item.name)) for item in fields(value)
        }
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]"
            if str(key).lower() in REDACTED_KEYS
            else serialize(item)
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list, set, frozenset)):
        return [serialize(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value


__all__ = tuple(name for name in globals() if not name.startswith("_"))
