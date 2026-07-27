"""Framework-neutral API facade for event streaming endpoints."""

from typing import Any

from ..platform import EventScope, EventStreamingPlatform


class EventStreamingAPI:
    ROUTES = (
        "/event-streams",
        "/topics",
        "/publish",
        "/subscribe",
        "/replay",
        "/checkpoints",
    )

    def __init__(self, platform: EventStreamingPlatform) -> None:
        self.platform = platform

    def get(self, path: str, scope: EventScope) -> Any:
        if path == "/event-streams":
            return self.platform.dashboard(scope)["streams"]
        if path == "/topics":
            return self.platform.dashboard(scope)["topics"]
        if path == "/checkpoints":
            return self.platform.dashboard(scope)["replay"]["checkpoints"]
        raise KeyError("Unknown API route.")

    def post(self, path: str, scope: EventScope, body: dict[str, Any]) -> Any:
        if path == "/publish":
            return self.platform.publish(scope=scope, **body).to_dict()
        if path == "/subscribe":
            return [
                event.to_dict() for event in self.platform.pull(scope=scope, **body)
            ]
        if path == "/replay":
            return [
                event.to_dict() for event in self.platform.replay(scope=scope, **body)
            ]
        raise KeyError("Unknown API route.")
