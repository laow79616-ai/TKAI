"""Ordered fallback policy example without provider or network calls."""

from __future__ import annotations

from tkai.ai import (
    FallbackCandidate,
    FallbackEngine,
    FallbackPolicy,
    ProviderTimeoutError,
)


def run() -> str:
    """Return the second candidate after a safe temporary failure on the first."""

    def operation(candidate: str) -> str:
        if candidate == "primary":
            raise ProviderTimeoutError("offline temporary failure")
        return candidate

    return FallbackEngine(FallbackPolicy(max_attempts=2)).execute(
        (
            FallbackCandidate("primary", "primary"),
            FallbackCandidate("backup", "backup"),
        ),
        operation,
    )


if __name__ == "__main__":
    print(run())
