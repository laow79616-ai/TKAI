"""Explicit adapters that record platform signals without taking over runtimes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tkai.observability import Event, EventBus

from .manager import TelemetryManager

if TYPE_CHECKING:
    from tkai.distributed import FailoverSnapshot, ServiceInstance


class TelemetryIntegration:
    """Optional bridge for EventBus, Runtime, Retry, failover, and discovery signals."""

    def __init__(self, manager: TelemetryManager) -> None:
        self.manager = manager
        self._event_bus: EventBus | None = None

    def attach_event_bus(self, event_bus: EventBus) -> None:
        """Subscribe once to a supplied EventBus; callers retain bus ownership."""
        if self._event_bus is event_bus:
            return
        self.detach_event_bus()
        event_bus.subscribe(self.record_event)
        self._event_bus = event_bus

    def detach_event_bus(self) -> None:
        """Remove the optional subscription without clearing any external handlers."""
        if self._event_bus is not None:
            self._event_bus.unsubscribe(self.record_event)
            self._event_bus = None

    def record_event(self, event: Event) -> None:
        """Record one EventBus delivery using only safe event name metadata."""
        self.manager.platform.counter("telemetry.eventbus.events", event=event.name)

    def record_retry(self, *, attempted: bool) -> None:
        """Record an explicit retry decision without controlling retry execution."""
        self.manager.platform.counter(
            "telemetry.retry.decisions", attempted="true" if attempted else "false"
        )

    def record_failover(self, snapshot: FailoverSnapshot) -> None:
        """Record a failover snapshot without affecting backend state transitions."""
        self.manager.platform.gauge(
            "telemetry.failover.active",
            1.0,
            state=snapshot.state.value,
            backend=snapshot.active_backend,
        )

    def record_service_lookup(
        self, service: str, instances: tuple[ServiceInstance, ...]
    ) -> None:
        """Record result size without retaining endpoint or metadata values."""
        self.manager.platform.histogram(
            "telemetry.service_discovery.instances",
            float(len(instances)),
            service=service,
        )

    def close(self) -> None:
        """Release optional EventBus subscription; manager lifecycle is independent."""
        self.detach_event_bus()
