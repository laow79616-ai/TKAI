"""Bounded, synchronous, in-process V7 event coordination framework."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import replace
from hashlib import sha256
from threading import RLock
from time import monotonic
from uuid import uuid4

from tkai.v7.security import AccessController, Principal, filter_secrets

from .contracts import (
    DeadLetterRecord,
    DeliveryMode,
    DeliveryResult,
    EventContract,
    EventEnvelope,
    EventFilter,
    EventLifecycle,
    EventModel,
    FailureClass,
    IdempotencyRecord,
    OrderingMode,
    Publisher,
    ReplayPolicy,
    ReplayRequest,
    RetryPolicy,
    RetryRecord,
    Subscriber,
    SubscriberHandler,
    Subscription,
    serialize,
    utc_now,
)

METRIC_NAMES = (
    "v7_event_fabric_events_registered_total",
    "v7_event_fabric_events_published_total",
    "v7_event_fabric_events_routed_total",
    "v7_event_fabric_events_dispatched_total",
    "v7_event_fabric_events_delivered_total",
    "v7_event_fabric_events_failed_total",
    "v7_event_fabric_events_retried_total",
    "v7_event_fabric_events_dead_lettered_total",
    "v7_event_fabric_events_replayed_total",
    "v7_event_fabric_duplicates_total",
    "v7_event_fabric_delivery_latency_seconds",
    "v7_event_fabric_queue_depth",
    "v7_event_fabric_subscriber_availability",
)


class EventFabricError(RuntimeError):
    pass


class EventValidationError(EventFabricError):
    pass


class DispatchQueueFull(EventFabricError):
    pass


class ReplayRejected(EventFabricError):
    pass


class AuditLog:
    def __init__(self) -> None:
        self._records: list[dict[str, object]] = []

    def record(
        self,
        action: str,
        reference: str,
        *,
        actor: str = "system",
        details: Mapping[str, object] | None = None,
    ) -> str:
        audit_id = str(uuid4())
        self._records.append(
            {
                "audit_id": audit_id,
                "timestamp": utc_now(),
                "action": action,
                "reference": reference,
                "actor": actor,
                "details": filter_secrets(details or {}),
            }
        )
        return audit_id

    def list(self, reference: str | None = None) -> tuple[dict[str, object], ...]:
        return tuple(
            dict(item)
            for item in self._records
            if reference is None or item["reference"] == reference
        )


class Metrics:
    def __init__(self) -> None:
        self._values: dict[str, float] = {name: 0.0 for name in METRIC_NAMES}

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRIC_NAMES:
            raise KeyError(name)
        self._values[name] += amount

    def set(self, name: str, value: float) -> None:
        if name not in METRIC_NAMES:
            raise KeyError(name)
        self._values[name] = value

    def snapshot(self) -> dict[str, float]:
        return {name: float(self._values[name]) for name in METRIC_NAMES}


class TracingHooks:
    def __init__(self) -> None:
        self._hooks: list[Callable[[str, Mapping[str, object]], None]] = []

    def register(self, hook: Callable[[str, Mapping[str, object]], None]) -> None:
        self._hooks.append(hook)

    def emit(self, name: str, attributes: Mapping[str, object]) -> None:
        safe = filter_secrets(attributes)
        for hook in self._hooks:
            hook(name, safe)


class EventRegistry:
    """Thread-safe contract, actor, subscription, and lifecycle registry."""

    def __init__(self) -> None:
        self._contracts: dict[tuple[str, str], EventContract] = {}
        self._publishers: dict[str, Publisher] = {}
        self._subscribers: dict[str, Subscriber] = {}
        self._handlers: dict[str, SubscriberHandler] = {}
        self._subscriptions: dict[str, Subscription] = {}
        self._filters: dict[str, EventFilter] = {}
        self._lifecycle: dict[str, list[EventLifecycle]] = {}
        self._metadata: dict[str, set[str]] = {}
        self._lock = RLock()
        self.audit = AuditLog()
        self.metrics = Metrics()

    def register_event(self, contract: EventContract) -> EventContract:
        key = (contract.event_type, str(contract.version))
        with self._lock:
            if key in self._contracts:
                raise ValueError(f"event contract already registered: {key}")
            safe = replace(contract, metadata=filter_secrets(contract.metadata))
            self._contracts[key] = safe
            for name, value in safe.metadata.items():
                self._metadata.setdefault(f"{name}:{value}", set()).add(safe.event_type)
            self.metrics.increment("v7_event_fabric_events_registered_total")
            self.audit.record("registered", safe.event_type)
            return safe

    register_event_type = register_event
    register_event_version = register_event

    def schema(self, event_type: str, version: object) -> Mapping[str, object]:
        return self.contract(event_type, version).schema

    def contract(self, event_type: str, version: object) -> EventContract:
        try:
            return self._contracts[(event_type, str(version))]
        except KeyError as error:
            raise EventValidationError(
                f"unregistered event contract: {event_type}@{version}"
            ) from error

    def contracts(self) -> tuple[EventContract, ...]:
        return tuple(self._contracts[key] for key in sorted(self._contracts))

    def compatible(self, event_type: str, version: object) -> tuple[EventContract, ...]:
        return tuple(
            contract
            for contract in self.contracts()
            if contract.event_type == event_type
            and contract.compatibility.supports(version)  # type: ignore[arg-type]
        )

    def register_publisher(self, publisher: Publisher) -> Publisher:
        if publisher.publisher_id in self._publishers:
            raise ValueError(f"publisher already registered: {publisher.publisher_id}")
        safe = replace(publisher, metadata=filter_secrets(publisher.metadata))
        self._publishers[safe.publisher_id] = safe
        self.audit.record("publisher_registered", safe.publisher_id)
        return safe

    def publisher(self, publisher_id: str) -> Publisher:
        return self._publishers[publisher_id]

    def publishers(self, event_type: str | None = None) -> tuple[Publisher, ...]:
        return tuple(
            item
            for item in sorted(self._publishers.values(), key=lambda x: x.publisher_id)
            if event_type is None or event_type in item.event_types
        )

    def register_subscriber(
        self, subscriber: Subscriber, handler: SubscriberHandler | None = None
    ) -> Subscriber:
        if subscriber.subscriber_id in self._subscribers:
            raise ValueError(
                f"subscriber already registered: {subscriber.subscriber_id}"
            )
        safe = replace(subscriber, metadata=filter_secrets(subscriber.metadata))
        self._subscribers[safe.subscriber_id] = safe
        if handler is not None:
            self._handlers[safe.subscriber_id] = handler
        self.audit.record("subscriber_registered", safe.subscriber_id)
        return safe

    def subscriber(self, subscriber_id: str) -> Subscriber:
        return self._subscribers[subscriber_id]

    def subscribers(self) -> tuple[Subscriber, ...]:
        return tuple(sorted(self._subscribers.values(), key=lambda x: x.subscriber_id))

    def handler(self, subscriber_id: str) -> SubscriberHandler:
        return self._handlers[subscriber_id]

    def register_filter(self, filter_id: str, event_filter: EventFilter) -> None:
        self._filters[filter_id] = event_filter

    def event_filter(self, filter_id: str | None) -> EventFilter:
        return self._filters.get(filter_id or "", EventFilter())

    def register_subscription(self, subscription: Subscription) -> Subscription:
        if subscription.subscription_id in self._subscriptions:
            raise ValueError(
                f"subscription already registered: {subscription.subscription_id}"
            )
        if subscription.subscriber_reference not in self._subscribers:
            raise EventValidationError("subscription references unknown subscriber")
        safe = replace(subscription, metadata=filter_secrets(subscription.metadata))
        self._subscriptions[safe.subscription_id] = safe
        self.audit.record("subscription_registered", safe.subscription_id)
        return safe

    def subscriptions(self, event_type: str | None = None) -> tuple[Subscription, ...]:
        return tuple(
            item
            for item in sorted(
                self._subscriptions.values(),
                key=lambda x: (x.priority, x.subscription_id),
            )
            if event_type is None or item.event_type == event_type
        )

    def metadata_lookup(self, key: str, value: object) -> tuple[str, ...]:
        return tuple(sorted(self._metadata.get(f"{key}:{value}", set())))

    def transition(self, event_id: str, state: EventLifecycle) -> None:
        self._lifecycle.setdefault(event_id, []).append(state)
        self.audit.record(state.value, event_id)

    def lifecycle(self, event_id: str) -> tuple[EventLifecycle, ...]:
        return tuple(self._lifecycle.get(event_id, ()))


class EventSecurity:
    """RBAC-compatible local authorization and isolation checks."""

    def __init__(self, access: AccessController | None = None) -> None:
        self.access = access

    def authorize(
        self,
        principal: Principal | None,
        capability: str,
        *,
        event: EventModel | None = None,
        tenant_reference: str | None = None,
        workspace_reference: str | None = None,
    ) -> None:
        if self.access is not None:
            if principal is None:
                raise PermissionError("principal required")
            self.access.require(principal, capability)
        if event is not None:
            if tenant_reference and event.tenant_reference != tenant_reference:
                raise PermissionError("tenant isolation violation")
            if workspace_reference and event.workspace_reference != workspace_reference:
                raise PermissionError("workspace isolation violation")


class EventRouter:
    def __init__(self, registry: EventRegistry) -> None:
        self.registry = registry

    def route(self, envelope: EventEnvelope) -> tuple[Subscription, ...]:
        event = envelope.event
        primary: list[Subscription] = []
        fallback: list[Subscription] = []
        for subscription in self.registry.subscriptions(event.event_type):
            subscriber = self.registry.subscriber(subscription.subscriber_reference)
            if subscription.status != "active":
                continue
            if subscriber.health_state != "healthy":
                continue
            if subscriber.lifecycle_state != "active":
                continue
            if not subscription.versions.supports(event.event_version):
                continue
            if subscription.tenant_reference not in (None, event.tenant_reference):
                continue
            if subscription.workspace_reference not in (
                None,
                event.workspace_reference,
            ):
                continue
            if not self.registry.event_filter(subscription.filter_reference).matches(
                event
            ):
                continue
            (fallback if subscription.fallback else primary).append(subscription)
        result = primary or fallback
        if result:
            self.registry.metrics.increment("v7_event_fabric_events_routed_total")
            self.registry.transition(event.event_id, EventLifecycle.ROUTED)
        return tuple(result)


class DispatchQueue:
    """Explicitly drained bounded queue; it never creates background workers."""

    def __init__(self, maximum_size: int = 1000, maximum_batch_size: int = 100) -> None:
        if maximum_size < 1 or maximum_batch_size < 1:
            raise ValueError("queue and batch limits must be positive")
        self.maximum_size = maximum_size
        self.maximum_batch_size = min(maximum_batch_size, maximum_size)
        self._items: deque[tuple[EventEnvelope, Subscription]] = deque()
        self.paused = False
        self.cancelled = False
        self.shutting_down = False
        self.kill_switch = False
        self.dispatch_timeout_seconds = 5.0

    @property
    def depth(self) -> int:
        return len(self._items)

    def put(self, item: tuple[EventEnvelope, Subscription]) -> None:
        if self.shutting_down or self.kill_switch:
            raise RuntimeError("dispatch unavailable")
        if len(self._items) >= self.maximum_size:
            raise DispatchQueueFull("bounded dispatch queue is full")
        self._items.append(item)

    def batch(
        self, size: int | None = None
    ) -> tuple[tuple[EventEnvelope, Subscription], ...]:
        if self.paused or self.cancelled or self.shutting_down or self.kill_switch:
            return ()
        limit = min(size or self.maximum_batch_size, self.maximum_batch_size)
        return tuple(self._items.popleft() for _ in range(min(limit, len(self._items))))


class IdempotencyStore:
    def __init__(self, maximum_records: int = 10000) -> None:
        self.maximum_records = maximum_records
        self._records: dict[str, IdempotencyRecord] = {}

    @staticmethod
    def fingerprint(envelope: EventEnvelope) -> str:
        value = f"{envelope.event.event_id}:{envelope.payload_hash}"
        return sha256(value.encode()).hexdigest()

    def check(
        self, key: str, envelope: EventEnvelope, subscriber_scope: str
    ) -> IdempotencyRecord:
        scoped = f"{subscriber_scope}:{key}"
        fingerprint = self.fingerprint(envelope)
        existing = self._records.get(scoped)
        if existing and existing.fingerprint == fingerprint:
            return replace(existing, duplicate=True, outcome="duplicate")
        if len(self._records) >= self.maximum_records:
            self._records.pop(next(iter(self._records)))
        record = IdempotencyRecord(key, fingerprint, subscriber_scope)
        self._records[scoped] = record
        return record

    def records(self) -> tuple[IdempotencyRecord, ...]:
        return tuple(self._records.values())


class EventFabric:
    """Composition root for explicit publication, routing, and bounded delivery."""

    def __init__(
        self,
        registry: EventRegistry | None = None,
        *,
        maximum_queue_size: int = 1000,
        maximum_batch_size: int = 100,
        maximum_delivery_attempts: int = 3,
        security: EventSecurity | None = None,
    ) -> None:
        self.registry = registry or EventRegistry()
        self.router = EventRouter(self.registry)
        self.queue = DispatchQueue(maximum_queue_size, maximum_batch_size)
        self.maximum_delivery_attempts = max(1, maximum_delivery_attempts)
        self.security = security or EventSecurity()
        self.tracing = TracingHooks()
        self.idempotency = IdempotencyStore()
        self.retry_policies: dict[str, RetryPolicy] = {"default": RetryPolicy()}
        self.replay_policies: dict[str, ReplayPolicy] = {"default": ReplayPolicy()}
        self.events: dict[str, EventEnvelope] = {}
        self.deliveries: list[DeliveryResult] = []
        self.retry_history: list[RetryRecord] = []
        self.dead_letters: list[DeadLetterRecord] = []
        self.replays: list[ReplayRequest] = []

    def publish(
        self,
        publisher_reference: str,
        event: EventModel,
        *,
        principal: Principal | None = None,
        payload_metadata: Mapping[str, object] | None = None,
    ) -> EventEnvelope:
        publisher = self.registry.publisher(publisher_reference)
        if event.event_type not in publisher.event_types:
            raise EventValidationError("publisher is not registered for event type")
        self.registry.contract(event.event_type, event.event_version)
        self.security.authorize(
            principal, f"event.publish:{event.event_type}", event=event
        )
        envelope = EventEnvelope.create(event, payload_metadata=payload_metadata)
        if not envelope.verify():
            raise EventValidationError("payload integrity validation failed")
        self.registry.transition(event.event_id, EventLifecycle.REGISTERED)
        self.registry.transition(event.event_id, EventLifecycle.VALIDATED)
        self.events[event.event_id] = envelope
        self.registry.metrics.increment("v7_event_fabric_events_published_total")
        self.registry.transition(event.event_id, EventLifecycle.PUBLISHED)
        self.tracing.emit("event.published", {"event_id": event.event_id})
        for subscription in self.router.route(envelope):
            self.queue.put((envelope, subscription))
        self.registry.metrics.set(
            "v7_event_fabric_queue_depth", float(self.queue.depth)
        )
        return envelope

    def dispatch(self, batch_size: int | None = None) -> tuple[DeliveryResult, ...]:
        results: list[DeliveryResult] = []
        for envelope, subscription in self.queue.batch(batch_size):
            self.registry.metrics.increment("v7_event_fabric_events_dispatched_total")
            self.registry.transition(envelope.event.event_id, EventLifecycle.DISPATCHED)
            results.append(self._deliver(envelope, subscription))
        self.registry.metrics.set(
            "v7_event_fabric_queue_depth", float(self.queue.depth)
        )
        return tuple(results)

    def _deliver(
        self, envelope: EventEnvelope, subscription: Subscription
    ) -> DeliveryResult:
        event_id = envelope.event.event_id
        duplicate = self.idempotency.check(
            event_id, envelope, subscription.subscriber_reference
        )
        if duplicate.duplicate:
            self.registry.metrics.increment("v7_event_fabric_duplicates_total")
            return DeliveryResult(
                event_id,
                subscription.subscriber_reference,
                delivered=True,
                acknowledged=True,
                attempts=0,
                reason="duplicate suppressed",
            )
        policy = self.retry_policies.get(subscription.retry_policy, RetryPolicy())
        maximum = min(policy.maximum_attempts, self.maximum_delivery_attempts)
        attempts = (
            1 if subscription.delivery_mode is DeliveryMode.AT_MOST_ONCE else maximum
        )
        started = monotonic()
        failure: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                outcome = self.registry.handler(subscription.subscriber_reference)(
                    envelope
                )
                acknowledged = bool(
                    outcome is True
                    or getattr(outcome, "acknowledged", False)
                    or subscription.delivery_mode is DeliveryMode.BEST_EFFORT
                )
                latency = monotonic() - started
                result = DeliveryResult(
                    event_id,
                    subscription.subscriber_reference,
                    delivered=True,
                    acknowledged=acknowledged,
                    attempts=attempt,
                    latency_seconds=latency,
                )
                self.deliveries.append(result)
                self.registry.metrics.increment(
                    "v7_event_fabric_events_delivered_total"
                )
                self.registry.metrics.increment(
                    "v7_event_fabric_delivery_latency_seconds", latency
                )
                self.registry.transition(event_id, EventLifecycle.DELIVERED)
                if acknowledged:
                    self.registry.transition(event_id, EventLifecycle.ACKNOWLEDGED)
                return result
            except Exception as error:  # noqa: BLE001 - subscriber isolation boundary
                failure = error
                failure_class = getattr(error, "failure_class", FailureClass.TRANSIENT)
                if not isinstance(failure_class, FailureClass):
                    failure_class = FailureClass.TRANSIENT
                if attempt < attempts and failure_class in policy.retryable:
                    record = RetryRecord(
                        event_id,
                        subscription.subscriber_reference,
                        attempt,
                        failure_class,
                        policy.delay(attempt),
                    )
                    self.retry_history.append(record)
                    self.registry.metrics.increment(
                        "v7_event_fabric_events_retried_total"
                    )
                    self.registry.transition(event_id, EventLifecycle.RETRYING)
                    continue
                break
        latency = monotonic() - started
        failure_class = FailureClass.TRANSIENT
        reason = type(failure).__name__ if failure is not None else "delivery failed"
        result = DeliveryResult(
            event_id,
            subscription.subscriber_reference,
            delivered=False,
            attempts=attempts,
            latency_seconds=latency,
            failure_class=failure_class,
            reason=reason,
        )
        self.deliveries.append(result)
        self.registry.metrics.increment("v7_event_fabric_events_failed_total")
        audit_id = self.registry.audit.record("delivery_failed", event_id)
        self.dead_letters.append(
            DeadLetterRecord(
                str(uuid4()),
                event_id,
                reason,
                attempts,
                subscription.subscriber_reference,
                subscription.dead_letter_policy,
                audit_reference=audit_id,
            )
        )
        self.registry.metrics.increment("v7_event_fabric_events_dead_lettered_total")
        self.registry.transition(event_id, EventLifecycle.DEAD_LETTERED)
        return result

    def replay(self, request: ReplayRequest) -> tuple[EventEnvelope, ...]:
        policy = ReplayPolicy()
        if policy.approval_required and not request.approval_reference:
            raise ReplayRejected("explicit replay approval is required")
        if request.maximum_results > policy.maximum_events:
            raise ReplayRejected("replay result bound exceeds policy")
        prior = sum(
            item.event_reference == request.event_reference for item in self.replays
        )
        if prior >= min(request.maximum_replays, policy.maximum_replays):
            raise ReplayRejected("bounded replay count exhausted")
        matches = tuple(
            envelope
            for event_id, envelope in sorted(self.events.items())
            if request.event_reference in (None, event_id)
        )[: request.maximum_results]
        completed = replace(request, status="completed")
        self.replays.append(completed)
        for envelope in matches:
            self.registry.transition(envelope.event.event_id, EventLifecycle.REPLAYED)
            self.registry.metrics.increment("v7_event_fabric_events_replayed_total")
        self.registry.audit.record(
            "replayed", request.request_id, details={"count": len(matches)}
        )
        return matches

    def ordering_key(
        self,
        event: EventModel,
        mode: OrderingMode,
        partition_key_reference: str | None = None,
    ) -> str | None:
        if mode is OrderingMode.NONE:
            return None
        if mode is OrderingMode.SOURCE:
            return event.source
        if mode is OrderingMode.SUBJECT:
            return event.subject
        if mode is OrderingMode.CORRELATION:
            return event.correlation_id
        if not partition_key_reference:
            raise ValueError("explicit partition key reference required")
        return partition_key_reference

    def health(self) -> dict[str, object]:
        subscribers = self.registry.subscribers()
        available = sum(item.health_state == "healthy" for item in subscribers)
        availability = available / len(subscribers) if subscribers else 1.0
        self.registry.metrics.set(
            "v7_event_fabric_subscriber_availability", availability
        )
        ready = not self.queue.kill_switch and not self.queue.shutting_down
        return {
            "status": "healthy" if ready else "degraded",
            "live": not self.queue.shutting_down,
            "ready": ready and not self.queue.paused,
            "registry": "healthy",
            "publishers": "healthy",
            "subscribers": "healthy" if availability == 1.0 else "degraded",
            "dispatch": "paused" if self.queue.paused else "healthy",
            "delivery": "healthy",
            "retry": "healthy",
            "dead_letter": "healthy",
            "replay": "healthy",
            "diagnostics": {
                "queue_depth": self.queue.depth,
                "queue_capacity": self.queue.maximum_size,
                "subscriber_availability": availability,
            },
        }

    def snapshot(self) -> dict[str, object]:
        return {
            "catalog": serialize(self.registry.contracts()),
            "registry": {
                "contracts": len(self.registry.contracts()),
                "publishers": len(self.registry.publishers()),
                "subscribers": len(self.registry.subscribers()),
                "subscriptions": len(self.registry.subscriptions()),
            },
            "publishers": serialize(self.registry.publishers()),
            "subscribers": serialize(self.registry.subscribers()),
            "subscriptions": serialize(self.registry.subscriptions()),
            "routing": {
                item.event_type: [
                    subscription.subscription_id
                    for subscription in self.registry.subscriptions(item.event_type)
                ]
                for item in self.registry.contracts()
            },
            "dispatch": {
                "queue_depth": self.queue.depth,
                "queue_capacity": self.queue.maximum_size,
                "batch_limit": self.queue.maximum_batch_size,
                "paused": self.queue.paused,
                "cancelled": self.queue.cancelled,
                "shutdown": self.queue.shutting_down,
                "kill_switch": self.queue.kill_switch,
                "dispatch_timeout_seconds": self.queue.dispatch_timeout_seconds,
            },
            "delivery": serialize(self.deliveries),
            "retry": serialize(self.retry_history),
            "dead_letter": serialize(self.dead_letters),
            "replay": serialize(self.replays),
            "ordering": {
                "global_ordering": False,
                "modes": [x.value for x in OrderingMode],
            },
            "idempotency": serialize(self.idempotency.records()),
            "health": self.health(),
            "metrics": self.registry.metrics.snapshot(),
            "audit": serialize(self.registry.audit.list()),
            "lifecycle": {
                event_id: serialize(self.registry.lifecycle(event_id))
                for event_id in sorted(self.events)
            },
        }


GLOBAL_FABRIC = EventFabric()


def structured_event(
    name: str, reference: str, fields: Mapping[str, object] | None = None
) -> dict[str, object]:
    return {
        "name": name,
        "reference": reference,
        "fields": filter_secrets(fields or {}),
    }


__all__ = (
    "AuditLog",
    "DispatchQueue",
    "DispatchQueueFull",
    "EventFabric",
    "EventFabricError",
    "EventRegistry",
    "EventRouter",
    "EventSecurity",
    "EventValidationError",
    "GLOBAL_FABRIC",
    "IdempotencyStore",
    "METRIC_NAMES",
    "Metrics",
    "ReplayRejected",
    "TracingHooks",
    "structured_event",
)
