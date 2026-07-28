"""Stable citation generation."""

import hashlib

from knowledge_platform.models import Chunk, Citation


def create_citation(
    chunk: Chunk,
    *,
    page: int | None = None,
    section: str | None = None,
    source_url: str | None = None,
) -> Citation:
    identity = f"{chunk.document_id}\0{chunk.id}\0{page}\0{section}".encode()
    return Citation(
        "cite_" + hashlib.sha256(identity).hexdigest()[:20],
        chunk.document_id,
        chunk.id,
        page,
        section,
        source_url,
        chunk.text[:500],
    )
