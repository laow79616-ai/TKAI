"""Security utilities for browser runtime references and encrypted state."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path, PurePath
from typing import Any


def validate_directory_reference(reference: str, allowed_root: Path | None) -> None:
    if not reference:
        return
    path = PurePath(reference)
    if ".." in path.parts:
        raise ValueError("Path traversal is not allowed in directory references.")
    if path.is_absolute():
        if allowed_root is None:
            raise ValueError("Absolute profile paths require an allowed root.")
        resolved = Path(reference).resolve()
        root = allowed_root.resolve()
        if resolved != root and root not in resolved.parents:
            raise ValueError("Profile directory is outside the allowed root.")


class EncryptedStorageState:
    """Authenticated encrypted persistence without plaintext state at rest."""

    def __init__(self, key: bytes | None = None) -> None:
        self._key = key or os.urandom(32)
        if len(self._key) < 32:
            raise ValueError("Encryption key must contain at least 32 bytes.")
        self._records: dict[str, bytes] = {}

    def export(self, reference: str, state: dict[str, Any]) -> str:
        if not reference:
            raise ValueError("Storage reference is required.")
        raw = json.dumps(state, separators=(",", ":"), sort_keys=True).encode()
        nonce = os.urandom(16)
        stream = hashlib.sha256(self._key + nonce).digest()
        ciphertext = bytes(v ^ stream[i % len(stream)] for i, v in enumerate(raw))
        tag = hmac.new(self._key, nonce + ciphertext, hashlib.sha256).digest()
        self._records[reference] = nonce + tag + ciphertext
        return reference

    def import_state(self, reference: str) -> dict[str, Any]:
        payload = self._records[reference]
        nonce, tag, ciphertext = payload[:16], payload[16:48], payload[48:]
        expected = hmac.new(self._key, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected):
            raise ValueError("Encrypted storage state failed integrity validation.")
        stream = hashlib.sha256(self._key + nonce).digest()
        raw = bytes(v ^ stream[i % len(stream)] for i, v in enumerate(ciphertext))
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("Storage state must be an object.")
        return value

    def delete(self, reference: str) -> None:
        self._records.pop(reference, None)

    def contains_plaintext(self, value: str) -> bool:
        return any(value.encode() in record for record in self._records.values())
