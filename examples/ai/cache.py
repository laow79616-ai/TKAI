"""Opt-in in-memory cache example without provider calls or network access."""

from __future__ import annotations

from tkai.cache import CacheManager


def run() -> tuple[str, int]:
    """Show a read-through cache hit while retaining explicit caller ownership."""
    manager = CacheManager()
    calls = 0

    def create() -> str:
        nonlocal calls
        calls += 1
        return "cached:ok"

    first = manager.get_or_set("example", create)
    second = manager.get_or_set("example", create)
    assert first == second
    return first, calls


if __name__ == "__main__":
    print(run())
