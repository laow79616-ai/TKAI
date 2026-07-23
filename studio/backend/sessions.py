"""Session contracts; the architecture intentionally owns no browser session state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class StudioSession:
    """A host-provided session reference associated with an authenticated subject."""

    session_id: str
    subject: str
    expires_at: datetime


class SessionStore(Protocol):
    """Storage boundary for a host application's session implementation."""

    def get(self, session_id: str) -> StudioSession | None: ...
    def put(self, session: StudioSession) -> None: ...
    def delete(self, session_id: str) -> None: ...
