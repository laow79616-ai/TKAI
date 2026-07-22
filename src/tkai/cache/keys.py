"""Deterministic cache key builder for provider request-equivalent inputs."""

from __future__ import annotations

import hashlib
import json
from typing import Any


class CacheKeyBuilder:
    """Build stable versioned SHA-256 keys without embedding prompts in keys."""

    def __init__(self, version: str = "v1") -> None:
        if not version:
            raise ValueError("cache key version must not be empty")
        self.version = version

    def build(
        self,
        *,
        provider: str,
        model: str,
        prompt: Any,
        parameters: Any = None,
    ) -> str:
        """Hash canonical request data so equivalent input produces one key."""
        if not provider or not model:
            raise ValueError("provider and model must not be empty")
        payload = {
            "version": self.version,
            "provider": provider,
            "model": model,
            "prompt_hash": self._hash(prompt),
            "parameter_hash": self._hash(parameters),
        }
        return self._hash(payload)

    @staticmethod
    def _hash(value: Any) -> str:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
