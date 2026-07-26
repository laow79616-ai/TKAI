"""Deterministic checksum and HMAC signing helpers."""

import hashlib
import hmac

from tkai.core.exceptions import PluginError


def checksum(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


class PluginSigner:
    def __init__(self, key: bytes) -> None:
        if not key:
            raise ValueError("signing key must not be empty")
        self._key = key

    def sign(self, payload: bytes) -> str:
        return hmac.new(self._key, payload, hashlib.sha256).hexdigest()

    def verify(self, payload: bytes, expected_checksum: str, signature: str) -> None:
        if not hmac.compare_digest(checksum(payload), expected_checksum):
            raise PluginError("Plugin checksum validation failed")
        if not hmac.compare_digest(self.sign(payload), signature):
            raise PluginError("Plugin signature validation failed")


__all__ = ("PluginSigner", "checksum")
