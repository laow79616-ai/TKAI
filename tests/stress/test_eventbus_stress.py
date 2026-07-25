"""Dedicated bounded EventBus concurrency and subscription-cleanup checks."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from tkai.observability import Event, EventBus


def test_eventbus_concurrent_publish_then_unsubscribe_has_no_stale_delivery() -> None:
    """Use a stable handler snapshot and remove subscriptions after publishers end."""
    bus = EventBus()
    delivered: list[int] = []
    lock = Lock()

    def handler(event: Event) -> None:
        with lock:
            delivered.append(int(event.data["sequence"]))

    bus.subscribe(handler)
    sequences = range(120)
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [
            executor.submit(bus.publish, Event("event", data={"sequence": sequence}))
            for sequence in sequences
        ]
        for future in futures:
            future.result(timeout=10)

    assert sorted(delivered) == list(sequences)
    bus.unsubscribe(handler)
    bus.publish(Event("after-unsubscribe", data={"sequence": 121}))
    assert len(delivered) == 120
    bus.clear()
    assert bus.events == []
