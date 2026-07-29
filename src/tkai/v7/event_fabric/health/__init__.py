from ..framework import EventFabric


def health_snapshot(fabric: EventFabric) -> dict[str, object]:
    return fabric.health()


__all__ = ("health_snapshot",)
