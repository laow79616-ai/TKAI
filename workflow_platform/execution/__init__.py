"""Execution controls."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExecutionOptions:
    mode: str = "sync"
    retries: int = 0
    timeout_seconds: float = 30
    checkpoint: bool = True

    def __post_init__(self) -> None:
        if self.mode not in {"sync", "async"}:
            raise ValueError("Execution mode must be sync or async.")
        if not 0 <= self.retries <= 10:
            raise ValueError("Retries exceed execution limits.")
        if not 0 < self.timeout_seconds <= 3600:
            raise ValueError("Timeout exceeds execution limits.")
