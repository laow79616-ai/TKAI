"""Typed models shared by the optional, provider-neutral Policy Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PolicyStage(str, Enum):
    """Explicit policy pipeline boundaries; no stage runs implicitly."""

    BEFORE_REQUEST = "before_request"
    BEFORE_ROUTING = "before_routing"
    BEFORE_PROVIDER = "before_provider"
    AFTER_PROVIDER = "after_provider"
    AFTER_RESPONSE = "after_response"


@dataclass(slots=True)
class PolicyContext:
    """Caller-owned mutable data passed through one explicit policy pipeline."""

    stage: PolicyStage
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    """Read-only result of policy evaluation before a policy is applied."""

    allowed: bool = True
    reason: str = "accepted"
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PolicyExecution:
    """One safe, serializable policy execution outcome."""

    policy: str
    stage: PolicyStage
    outcome: str
    reason: str = ""
