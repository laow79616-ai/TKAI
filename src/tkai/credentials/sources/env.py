"""Environment-variable credential source without external dependencies."""

from __future__ import annotations

import os
from collections.abc import Mapping

from ..models import Credential
from ..provider import CredentialProvider

_KEY_NAMES = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "google": "GOOGLE_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "qwen": "DASHSCOPE_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


class EnvironmentCredentialProvider(CredentialProvider):
    """Resolve known provider keys from an injected or process environment mapping."""

    def __init__(self, environment: Mapping[str, str] | None = None) -> None:
        self._environment = environment if environment is not None else os.environ

    def load(self, provider: str) -> Credential | None:
        """Read one non-empty provider key from the local environment mapping."""
        key_name = _KEY_NAMES.get(provider.lower())
        api_key = self._environment.get(key_name, "") if key_name else ""
        if not api_key:
            return None
        prefix = provider.upper().replace("-", "_")
        return Credential(
            provider=provider.lower(),
            api_key=api_key,
            organization=self._environment.get(f"{prefix}_ORGANIZATION"),
            base_url=self._environment.get(f"{prefix}_BASE_URL"),
            source=self.identifier(),
        )

    def supports(self, provider: str) -> bool:
        """Return whether a known key variable is non-empty."""
        key_name = _KEY_NAMES.get(provider.lower())
        return bool(key_name and self._environment.get(key_name))

    def identifier(self) -> str:
        """Return the safe source name."""
        return "environment"

    def providers(self) -> list[str]:
        """Return provider names with configured non-empty environment keys."""
        return sorted({name for name in _KEY_NAMES if self.supports(name)})
