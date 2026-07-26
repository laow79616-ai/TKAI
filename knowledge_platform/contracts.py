"""Contracts for parsing, chunking, embedding, retrieval, and evaluation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from .models import Chunk, Scope

SUPPORTED_EXTENSIONS = frozenset(
    {"pdf", "docx", "txt", "md", "markdown", "html", "csv", "json"}
)


@dataclass(frozen=True, slots=True)
class ParseError:
    code: str
    message: str
    recoverable: bool = False


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    text: str
    metadata: dict[str, object]
    pages: tuple[tuple[int, int], ...] = ()
    sections: tuple[tuple[str, int, int], ...] = ()
    errors: tuple[ParseError, ...] = ()


class DocumentParser(Protocol):
    def parse(self, content: bytes, *, encoding: str = "utf-8") -> ParsedDocument: ...


class TextParser:
    def parse(self, content: bytes, *, encoding: str = "utf-8") -> ParsedDocument:
        try:
            text = content.decode(encoding)
        except (LookupError, UnicodeDecodeError) as error:
            return ParsedDocument("", {}, errors=(ParseError("encoding", str(error)),))
        sections: list[tuple[str, int, int]] = []
        position = 0
        for line in text.splitlines(keepends=True):
            if line.lstrip().startswith("#"):
                sections.append(
                    (line.lstrip("# ").strip(), position, position + len(line))
                )
            position += len(line)
        return ParsedDocument(
            text, {"encoding": encoding}, ((0, len(text)),), tuple(sections)
        )


class Chunker(Protocol):
    def chunk(
        self, document_id: str, text: str, metadata: dict[str, object]
    ) -> tuple[Chunk, ...]: ...


class FixedSizeChunker:
    def __init__(self, size: int = 500, overlap: int = 50, token_limit: int = 1000):
        if size < 1 or overlap < 0 or overlap >= size or token_limit < 1:
            raise ValueError("Invalid chunk limits.")
        self.size, self.overlap, self.token_limit = size, overlap, token_limit

    def chunk(
        self, document_id: str, text: str, metadata: dict[str, object]
    ) -> tuple[Chunk, ...]:
        result: list[Chunk] = []
        start = 0
        while start < len(text):
            value = text[start : start + self.size]
            words = value.split()
            if len(words) > self.token_limit:
                value = " ".join(words[: self.token_limit])
            result.append(
                Chunk(
                    f"{document_id}:{len(result)}",
                    document_id,
                    value,
                    len(result),
                    len(value.split()),
                    dict(metadata),
                )
            )
            start += self.size - self.overlap
        return tuple(result)


class RecursiveChunker(FixedSizeChunker):
    def chunk(
        self, document_id: str, text: str, metadata: dict[str, object]
    ) -> tuple[Chunk, ...]:
        normalized = "\n\n".join(part.strip() for part in text.split("\n\n"))
        return super().chunk(document_id, normalized, metadata)


class SemanticChunker(Chunker, Protocol): ...


class EmbeddingProvider(Protocol):
    @property
    def dimension(self) -> int: ...
    def embed(self, texts: Sequence[str], *, timeout: float) -> list[list[float]]: ...


class EmbeddingCache(Protocol):
    def get(self, key: str) -> tuple[float, ...] | None: ...
    def put(self, key: str, value: tuple[float, ...]) -> None: ...


class EmbeddingService:
    def __init__(
        self,
        provider: EmbeddingProvider,
        *,
        batch_size: int = 32,
        retries: int = 2,
        timeout: float = 10,
    ):
        if batch_size < 1 or retries < 0 or timeout <= 0:
            raise ValueError("Invalid embedding limits.")
        self.provider = provider
        self.batch_size, self.retries, self.timeout = batch_size, retries, timeout

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        output: list[tuple[float, ...]] = []
        for offset in range(0, len(texts), self.batch_size):
            batch = texts[offset : offset + self.batch_size]
            last: Exception | None = None
            for _ in range(self.retries + 1):
                try:
                    vectors = self.provider.embed(batch, timeout=self.timeout)
                    if len(vectors) != len(batch) or any(
                        len(vector) != self.provider.dimension for vector in vectors
                    ):
                        raise ValueError("Embedding dimension validation failed.")
                    output.extend(tuple(vector) for vector in vectors)
                    last = None
                    break
                except (TimeoutError, ConnectionError) as error:
                    last = error
            if last:
                raise last
        return tuple(output)


@dataclass(frozen=True, slots=True)
class RetrievalQuery:
    text: str
    scope: Scope
    top_k: int = 10
    filters: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class Candidate:
    chunk: Chunk
    score: float


class Retriever(Protocol):
    def retrieve(self, query: RetrievalQuery) -> tuple[Candidate, ...]: ...


class VectorRetriever(Retriever, Protocol): ...


class KeywordRetriever(Retriever, Protocol): ...


class HybridRetriever:
    def __init__(self, vector: VectorRetriever, keyword: KeywordRetriever) -> None:
        self.vector, self.keyword = vector, keyword

    def retrieve(self, query: RetrievalQuery) -> tuple[Candidate, ...]:
        merged: dict[str, Candidate] = {}
        for item in (*self.vector.retrieve(query), *self.keyword.retrieve(query)):
            current = merged.get(item.chunk.id)
            if current is None or item.score > current.score:
                merged[item.chunk.id] = item
        return tuple(
            sorted(merged.values(), key=lambda item: item.score, reverse=True)[
                : query.top_k
            ]
        )


class Reranker(Protocol):
    def rerank(
        self, query: RetrievalQuery, values: tuple[Candidate, ...]
    ) -> tuple[Candidate, ...]: ...


def rank(
    values: tuple[Candidate, ...], *, threshold: float = 0, limit: int = 10
) -> tuple[Candidate, ...]:
    if limit < 1:
        raise ValueError("Result limit must be positive.")
    maximum = max((item.score for item in values), default=1) or 1
    result: dict[str, Candidate] = {}
    for item in values:
        normalized = Candidate(item.chunk, max(0, min(1, item.score / maximum)))
        current = result.get(item.chunk.id)
        if normalized.score >= threshold and (
            current is None or normalized.score > current.score
        ):
            result[item.chunk.id] = normalized
    return tuple(
        sorted(result.values(), key=lambda item: item.score, reverse=True)[:limit]
    )


@dataclass(frozen=True, slots=True)
class ConnectorRequest:
    resource_ids: tuple[str, ...]
    cursor: str | None = None
    limit: int = 100

    def __post_init__(self) -> None:
        if not self.resource_ids or not 1 <= self.limit <= 1000:
            raise ValueError("Bounded resources and limits are required.")


class Connector(Protocol):
    kind: str

    def import_documents(self, request: ConnectorRequest) -> tuple[bytes, ...]: ...


class GoogleDriveConnector(Connector, Protocol): ...


class SharePointConnector(Connector, Protocol): ...


class OneDriveConnector(Connector, Protocol): ...


class S3CompatibleConnector(Connector, Protocol): ...


class DatabaseConnector(Connector, Protocol): ...


class WebsiteConnector(Connector, Protocol): ...


class BoundedMemoryConnector:
    kind = "memory-reference"

    def __init__(self, resources: dict[str, bytes]) -> None:
        self.resources = dict(resources)

    def import_documents(self, request: ConnectorRequest) -> tuple[bytes, ...]:
        return tuple(
            self.resources[item]
            for item in request.resource_ids[: request.limit]
            if item in self.resources
        )


class WebUrlImporter(Protocol):
    """Fetch exactly one validated URL; implementations must not crawl."""

    def fetch(self, url: str, *, max_bytes: int, timeout: float) -> bytes: ...


@dataclass(frozen=True, slots=True)
class RegressionCase:
    query: str
    relevant_documents: tuple[str, ...]
    expected_citations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    relevance: float
    citation_accuracy: float
    coverage: float
    latency_seconds: float


class Benchmark(Protocol):
    def run(self, dataset: tuple[RegressionCase, ...]) -> EvaluationResult: ...
