"""Provider-neutral model profiles, defaults, and fallback selection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    AZURE_OPENAI = "azure_openai"
    LOCAL = "local"


@dataclass(frozen=True, slots=True)
class ModelProfile:
    profile_id: str
    provider: ModelProvider
    model: str
    endpoint: str | None = None
    parameters: dict[str, object] | None = None
    enabled: bool = True


class ModelRegistry:
    """Store configuration only; credentials stay in enterprise secret providers."""

    def __init__(self) -> None:
        self._profiles: dict[str, ModelProfile] = {}
        self._defaults: dict[str, str] = {}
        self._fallbacks: dict[str, tuple[str, ...]] = {}

    def register(self, profile: ModelProfile) -> ModelProfile:
        if profile.profile_id in self._profiles:
            raise ValueError(f"Model profile already exists: {profile.profile_id}")
        self._profiles[profile.profile_id] = profile
        return profile

    def profiles(
        self, provider: ModelProvider | None = None
    ) -> tuple[ModelProfile, ...]:
        items = (self._profiles[key] for key in sorted(self._profiles))
        return tuple(
            item for item in items if provider is None or item.provider is provider
        )

    def set_default(
        self, capability: str, profile_id: str, fallbacks: tuple[str, ...] = ()
    ) -> None:
        for candidate in (profile_id, *fallbacks):
            if candidate not in self._profiles:
                raise KeyError(f"Model profile not found: {candidate}")
        self._defaults[capability] = profile_id
        self._fallbacks[capability] = fallbacks

    def resolve(
        self, capability: str, unavailable: set[str] | None = None
    ) -> ModelProfile:
        blocked = unavailable or set()
        candidates = (
            self._defaults.get(capability, ""),
            *self._fallbacks.get(capability, ()),
        )
        for profile_id in candidates:
            profile = self._profiles.get(profile_id)
            if profile is not None and profile.enabled and profile_id not in blocked:
                return profile
        raise LookupError(f"No model available for capability: {capability}")


__all__ = ("ModelProfile", "ModelProvider", "ModelRegistry")
