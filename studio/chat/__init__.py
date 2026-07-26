"""Multi-session Chat Studio with streaming and portable histories."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Iterable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import RLock

from studio.metrics import StudioMetrics


@dataclass(frozen=True, slots=True)
class Attachment:
    name: str
    media_type: str
    uri: str
    size: int | None = None


@dataclass(frozen=True, slots=True)
class Message:
    role: str
    content: str
    attachments: tuple[Attachment, ...] = ()
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class ChatSession:
    session_id: str
    project_id: str
    messages: tuple[Message, ...] = ()


class ChatStudio:
    """Manage isolated sessions and provider-neutral token streams."""

    def __init__(
        self, id_factory: Callable[[str], str], metrics: StudioMetrics | None = None
    ) -> None:
        self._id_factory = id_factory
        self._metrics = metrics or StudioMetrics()
        self._items: dict[str, ChatSession] = {}
        self._lock = RLock()

    def create_session(self, project_id: str) -> ChatSession:
        item = ChatSession(self._id_factory("session"), project_id)
        with self._lock:
            self._items[item.session_id] = item
        self._metrics.increment("chat_sessions")
        return item

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        attachments: Iterable[Attachment] = (),
    ) -> Message:
        if role not in {"system", "user", "assistant", "tool"}:
            raise ValueError(f"Unsupported chat role: {role}")
        message = Message(role, content, tuple(attachments))
        with self._lock:
            current = self.get(session_id)
            self._items[session_id] = ChatSession(
                current.session_id, current.project_id, (*current.messages, message)
            )
        return message

    def get(self, session_id: str) -> ChatSession:
        with self._lock:
            try:
                return self._items[session_id]
            except KeyError as error:
                raise KeyError(f"Chat session not found: {session_id}") from error

    def history(self, session_id: str) -> tuple[Message, ...]:
        return self.get(session_id).messages

    async def stream(self, chunks: AsyncIterator[str]) -> AsyncIterator[str]:
        async for chunk in chunks:
            yield chunk

    def export_session(self, session_id: str) -> dict[str, object]:
        raw = asdict(self.get(session_id))
        for message in raw["messages"]:
            message["created_at"] = message["created_at"].isoformat()
        return {"schema_version": "2.3", "session": raw}

    def import_session(self, bundle: Mapping[str, object]) -> ChatSession:
        raw = bundle.get("session")
        if bundle.get("schema_version") != "2.3" or not isinstance(raw, Mapping):
            raise ValueError("Invalid Chat Studio bundle.")
        project_id = raw.get("project_id")
        messages = raw.get("messages", ())
        if not isinstance(project_id, str) or not isinstance(messages, (list, tuple)):
            raise ValueError("Invalid Chat Studio session.")
        session = self.create_session(project_id)
        for value in messages:
            if not isinstance(value, Mapping):
                raise ValueError("Invalid chat message.")
            attachments = tuple(
                Attachment(
                    str(item["name"]),
                    str(item["media_type"]),
                    str(item["uri"]),
                    int(item["size"]) if item.get("size") is not None else None,
                )
                for item in value.get("attachments", ())
                if isinstance(item, Mapping)
            )
            self.add_message(
                session.session_id,
                str(value.get("role", "")),
                str(value.get("content", "")),
                attachments,
            )
        return self.get(session.session_id)


__all__ = ("Attachment", "ChatSession", "ChatStudio", "Message")
