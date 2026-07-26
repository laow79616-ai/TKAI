"""Chunk/metadata compression and storage optimization helpers."""

from __future__ import annotations

import json
import zlib
from typing import Any


class MemoryCompressor:
    def compress_chunk(self, content: str) -> bytes:
        return zlib.compress(content.encode("utf-8"))

    def decompress_chunk(self, content: bytes) -> str:
        return zlib.decompress(content).decode("utf-8")

    def compress_metadata(self, metadata: dict[str, Any]) -> bytes:
        encoded = json.dumps(metadata, separators=(",", ":"), sort_keys=True)
        return zlib.compress(encoded.encode("utf-8"))

    def decompress_metadata(self, metadata: bytes) -> dict[str, Any]:
        value = json.loads(zlib.decompress(metadata).decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Compressed metadata is not an object.")
        return value

    def optimized_size(self, content: str, metadata: dict[str, Any]) -> int:
        return len(self.compress_chunk(content)) + len(
            self.compress_metadata(metadata)
        )
