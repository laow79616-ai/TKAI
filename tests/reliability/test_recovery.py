"""Focused recovery behavior after deterministic local failures."""

from __future__ import annotations

from tkai.observability import Event, EventBus


def test_event_bus_remains_usable_after_a_subscriber_fails_once() -> None:
    """A failing callback is isolated and does not duplicate future delivery."""
    bus = EventBus()
    calls: list[str] = []
    fail_once = True

    def unreliable(event: Event) -> None:
        nonlocal fail_once
        if fail_once:
            fail_once = False
            raise RuntimeError("injected")
        calls.append(f"unreliable:{event.name}")

    def reliable(event: Event) -> None:
        calls.append(f"reliable:{event.name}")

    bus.subscribe(unreliable)
    bus.subscribe(reliable)
    bus.publish(Event("first"))
    bus.publish(Event("second"))
    assert calls == ["reliable:first", "unreliable:second", "reliable:second"]
    assert [event.name for event in bus.events] == ["first", "second"]
