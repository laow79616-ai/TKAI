"""Encrypted cookie and session state storage."""

import hashlib
import hmac
import os


class EncryptedStateStore:
    def __init__(self, key: bytes | None = None) -> None:
        self._key = key or os.urandom(32)
        self._records: dict[str, bytes] = {}
        if len(self._key) < 32:
            raise ValueError("Encryption key must contain at least 32 bytes.")

    def put(self, reference: str, plaintext: str) -> None:
        if not reference or not plaintext:
            raise ValueError("Reference and secret state are required.")
        nonce = os.urandom(16)
        stream = hashlib.sha256(self._key + nonce).digest()
        raw = plaintext.encode()
        ciphertext = bytes(v ^ stream[i % len(stream)] for i, v in enumerate(raw))
        self._records[reference] = (
            nonce
            + hmac.new(self._key, nonce + ciphertext, hashlib.sha256).digest()
            + ciphertext
        )

    def get(self, reference: str) -> str:
        payload = self._records[reference]
        nonce, tag, ciphertext = payload[:16], payload[16:48], payload[48:]
        if not hmac.compare_digest(
            tag, hmac.new(self._key, nonce + ciphertext, hashlib.sha256).digest()
        ):
            raise ValueError("Encrypted state integrity validation failed.")
        stream = hashlib.sha256(self._key + nonce).digest()
        return bytes(
            v ^ stream[i % len(stream)] for i, v in enumerate(ciphertext)
        ).decode()

    def delete(self, reference: str) -> None:
        self._records.pop(reference, None)

    def contains_plaintext(self, value: str) -> bool:
        return any(value.encode() in data for data in self._records.values())
