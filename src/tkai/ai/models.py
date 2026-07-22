"""Provider-neutral AI request and response models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AIRequest:
    """A text-generation request independent of a provider SDK."""

    prompt: str
    model: str | None = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AIResponse:
    """A normalized text-generation response."""

    content: str
    provider: str
    model: str
    raw: Any = None
