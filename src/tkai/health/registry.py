"""In-memory passive health snapshots."""

from __future__ import annotations

from .models import HealthSnapshot


class HealthRegistry:
    def __init__(self) -> None:
        self._snapshots: dict[str, HealthSnapshot] = {}

    def get(self, provider: str) -> HealthSnapshot:
        return self._snapshots.get(provider, HealthSnapshot(provider))

    def list(self) -> list[HealthSnapshot]:
        return [self._snapshots[key] for key in sorted(self._snapshots)]

    def update(self, snapshot: HealthSnapshot) -> None:
        self._snapshots[snapshot.provider] = snapshot

    def reset(self, provider: str) -> HealthSnapshot:
        snapshot = HealthSnapshot(provider)
        self.update(snapshot)
        return snapshot

    def clear(self) -> None:
        self._snapshots.clear()
