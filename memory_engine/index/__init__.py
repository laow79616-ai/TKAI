"""Dependency-free keyword and similarity index."""

from __future__ import annotations

import re
from collections import Counter
from math import sqrt

from ..models import MemoryObject, SearchQuery, SearchResult

_TOKEN = re.compile(r"[\w-]+")


def _tokens(value: str) -> Counter[str]:
    return Counter(token.lower() for token in _TOKEN.findall(value))


def _cosine(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    dot = sum(value * right.get(key, 0) for key, value in left.items())
    left_norm = sqrt(sum(value * value for value in left.values()))
    right_norm = sqrt(sum(value * value for value in right.values()))
    return dot / (left_norm * right_norm)


class MemoryIndex:
    def __init__(self) -> None:
        self._documents: dict[str, tuple[MemoryObject, Counter[str]]] = {}

    def add(self, memory: MemoryObject) -> None:
        metadata = " ".join(f"{key} {value}" for key, value in memory.metadata.items())
        self._documents[memory.id] = (memory, _tokens(f"{memory.content} {metadata}"))

    def remove(self, memory_id: str) -> None:
        self._documents.pop(memory_id, None)

    def search(
        self, query: SearchQuery, candidates: set[str]
    ) -> tuple[SearchResult, ...]:
        query_tokens = _tokens(query.text)
        query_terms = set(query_tokens)
        results: list[SearchResult] = []
        for memory_id in candidates:
            entry = self._documents.get(memory_id)
            if entry is None:
                continue
            memory, tokens = entry
            if query.namespace is not None and memory.namespace != query.namespace:
                continue
            if any(
                memory.metadata.get(key) != value
                for key, value in query.metadata.items()
            ):
                continue
            keyword = len(query_terms & set(tokens)) / max(len(query_terms), 1)
            similarity = _cosine(query_tokens, tokens)
            if query.mode == "keyword":
                score = keyword
            elif query.mode == "similarity":
                score = similarity
            else:
                score = (keyword + similarity) / 2
            if score >= query.threshold:
                results.append(SearchResult(memory, round(score, 6)))
        results.sort(
            key=lambda item: (-item.score, -item.memory.priority, item.memory.id)
        )
        return tuple(results[: query.top_k])
