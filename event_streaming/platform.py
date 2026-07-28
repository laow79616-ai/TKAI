"""Tenant-safe in-memory Enterprise AI Event Streaming control plane."""

from __future__ import annotations

import fnmatch
import json
import re
import secrets
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from .metrics import EventStreamingMetrics


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class StreamStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DELETED = "deleted"


class DeliveryGuarantee(str, Enum):
    AT_LEAST_ONCE = "at_least_once"
    AT_MOST_ONCE = "at_most_once"


@dataclass(frozen=True, slots=True)
class EventScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"events:read"})

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class EventStream:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    topic: str
    schema: str
    version: str
    status: StreamStatus = StreamStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        return result


@dataclass(slots=True)
class Topic:
    name: str
    tenant: str
    workspace: str
    retention_seconds: int = 86_400
    partitions: int = 1
    replication: int = 1
    archive: bool = False
    compact: bool = False

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,254}", self.name):
            raise ValueError("Invalid topic name.")
        if self.retention_seconds < 1 or self.partitions < 1 or self.replication < 1:
            raise ValueError("Retention, partitions, and replication must be positive.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EventSchema:
    name: str
    version: str
    tenant: str
    workspace: str
    required: frozenset[str] = frozenset()
    properties: dict[str, str] = field(default_factory=dict)
    compatibility: str = "backward"

    def __post_init__(self) -> None:
        if self.compatibility not in {"none", "backward", "forward", "full"}:
            raise ValueError("Unsupported compatibility mode.")

    def validate(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            raise ValueError("Schema-validated event payloads must be objects.")
        missing = self.required - payload.keys()
        if missing:
            raise ValueError(f"Required payload fields are missing: {sorted(missing)}")
        types: dict[str, type[Any] | tuple[type[Any], ...]] = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "object": dict,
            "array": list,
        }
        for key, type_name in self.properties.items():
            if (
                key in payload
                and type_name in types
                and not isinstance(payload[key], types[type_name])
            ):
                raise ValueError(f"Payload field {key!r} must be {type_name}.")

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["required"] = sorted(self.required)
        return result


@dataclass(slots=True)
class Event:
    id: str
    topic: str
    payload: Any
    tenant: str
    workspace: str
    schema: str
    schema_version: str
    partition: int
    offset: int
    published_at: datetime
    publisher: str
    metadata: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    priority: int = 0
    transaction_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["published_at"] = self.published_at.isoformat()
        return result


@dataclass(slots=True)
class ConsumerGroup:
    name: str
    topic: str
    tenant: str
    workspace: str
    delivery: DeliveryGuarantee = DeliveryGuarantee.AT_LEAST_ONCE
    ordering: bool = True
    retry_limit: int = 3
    timeout_seconds: float = 30
    offsets: dict[int, int] = field(default_factory=dict)
    checkpoints: dict[int, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["delivery"] = self.delivery.value
        return result


@dataclass(slots=True)
class Subscription:
    id: str
    topic_pattern: str
    group: str
    tenant: str
    workspace: str
    mode: str = "pull"
    endpoint: str | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    priority: int = 0

    def __post_init__(self) -> None:
        if self.mode not in {"push", "pull"}:
            raise ValueError("Subscription mode must be push or pull.")
        if self.mode == "push" and not (
            self.endpoint and self.endpoint.startswith("https://")
        ):
            raise ValueError("Push subscriptions require an HTTPS endpoint.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RoutingRule:
    id: str
    topic_pattern: str
    destination_topic: str
    tenant: str
    workspace: str
    filters: dict[str, Any] = field(default_factory=dict)
    priority: int = 0


@dataclass(slots=True)
class DeadLetter:
    event: Event
    group: str
    reason: str
    attempts: int
    failed_at: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": self.event.to_dict(),
            "group": self.group,
            "reason": self.reason,
            "attempts": self.attempts,
            "failed_at": self.failed_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class AuditEntry:
    action: str
    actor: str
    tenant: str
    workspace: str
    occurred_at: datetime
    metadata: dict[str, Any]


class EventStreamingPlatform:
    """Reference event broker with explicit security and delivery semantics."""

    TRANSITIONS = {
        StreamStatus.DRAFT: {
            StreamStatus.ACTIVE,
            StreamStatus.ARCHIVED,
            StreamStatus.DELETED,
        },
        StreamStatus.ACTIVE: {StreamStatus.PAUSED, StreamStatus.ARCHIVED},
        StreamStatus.PAUSED: {StreamStatus.ACTIVE, StreamStatus.ARCHIVED},
        StreamStatus.ARCHIVED: {StreamStatus.DELETED},
        StreamStatus.DELETED: set(),
    }
    SECRET_KEYS = re.compile(
        r"(?:password|passwd|secret|token|api[_-]?key|authorization)", re.I
    )

    def __init__(self, *, max_payload_bytes: int = 1_048_576) -> None:
        if not 1 <= max_payload_bytes <= 10_485_760:
            raise ValueError("Payload limit must be between 1 byte and 10 MiB.")
        self.max_payload_bytes = max_payload_bytes
        self.streams: dict[str, EventStream] = {}
        self.topics: dict[str, Topic] = {}
        self.schemas: dict[tuple[str, str], EventSchema] = {}
        self.events: dict[str, list[list[Event]]] = {}
        self.groups: dict[str, ConsumerGroup] = {}
        self.subscriptions: dict[str, Subscription] = {}
        self.routes: dict[str, RoutingRule] = {}
        self.dead_letters: list[DeadLetter] = []
        self.audit: list[AuditEntry] = []
        self.publishers: set[tuple[str, str, str]] = set()
        self.subscribers: set[tuple[str, str, str]] = set()
        self.metrics = EventStreamingMetrics()

    @staticmethod
    def _key(name: str, scope: EventScope) -> str:
        return f"{scope.tenant}:{scope.workspace}:{name}"

    @staticmethod
    def _check(record: Any, scope: EventScope) -> None:
        if record.tenant != scope.tenant or record.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    @staticmethod
    def _require(scope: EventScope, permission: str) -> None:
        if (
            permission not in scope.permissions
            and "events:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    def _audit(self, action: str, scope: EventScope, **metadata: Any) -> None:
        safe = {k: v for k, v in metadata.items() if not self.SECRET_KEYS.search(k)}
        self.audit.append(
            AuditEntry(
                action, scope.actor, scope.tenant, scope.workspace, utcnow(), safe
            )
        )

    def create_topic(self, topic: Topic, scope: EventScope) -> Topic:
        self._require(scope, "events:manage")
        self._check(topic, scope)
        key = self._key(topic.name, scope)
        if key in self.topics:
            raise ValueError("Topic already exists.")
        self.topics[key] = topic
        self.events[key] = [[] for _ in range(topic.partitions)]
        self._audit("topic.create", scope, topic=topic.name)
        return topic

    def update_topic(self, name: str, scope: EventScope, **changes: Any) -> Topic:
        self._require(scope, "events:manage")
        topic = self.topics[self._key(name, scope)]
        allowed = {"retention_seconds", "replication", "archive", "compact"}
        if set(changes) - allowed:
            raise ValueError("Unsupported or unsafe topic update.")
        for field_name, value in changes.items():
            setattr(topic, field_name, value)
        topic.__post_init__()
        self._audit("topic.update", scope, topic=name)
        return topic

    def delete_topic(self, name: str, scope: EventScope) -> None:
        self._require(scope, "events:manage")
        key = self._key(name, scope)
        if any(
            stream.topic == name and stream.status is not StreamStatus.DELETED
            for stream in self.streams.values()
            if stream.tenant == scope.tenant and stream.workspace == scope.workspace
        ):
            raise ValueError("Topic is referenced by a live stream.")
        del self.topics[key]
        del self.events[key]
        self._audit("topic.delete", scope, topic=name)

    def register_schema(self, schema: EventSchema, scope: EventScope) -> EventSchema:
        self._require(scope, "events:schema")
        self._check(schema, scope)
        key = (self._key(schema.name, scope), schema.version)
        if key in self.schemas:
            raise ValueError("Schema version already exists.")
        previous = [item for (name, _), item in self.schemas.items() if name == key[0]]
        if previous and schema.compatibility in {"backward", "full"}:
            latest = previous[-1]
            if not latest.required <= schema.required:
                raise ValueError("Schema evolution removes required fields.")
        self.schemas[key] = schema
        self._audit(
            "schema.register", scope, schema=schema.name, version=schema.version
        )
        return schema

    def create_stream(self, stream: EventStream, scope: EventScope) -> EventStream:
        self._require(scope, "events:manage")
        self._check(stream, scope)
        if self._key(stream.topic, scope) not in self.topics:
            raise KeyError("Topic does not exist.")
        if (self._key(stream.schema, scope), stream.version) not in self.schemas:
            raise KeyError("Schema version does not exist.")
        if stream.id in self.streams:
            raise ValueError("Stream already exists.")
        self.streams[stream.id] = stream
        self._audit("stream.create", scope, stream_id=stream.id)
        return stream

    def set_stream_status(
        self, stream_id: str, status: StreamStatus, scope: EventScope
    ) -> EventStream:
        self._require(scope, "events:manage")
        stream = self.streams[stream_id]
        self._check(stream, scope)
        if status not in self.TRANSITIONS[stream.status]:
            raise ValueError("Invalid stream lifecycle transition.")
        stream.status = status
        self._audit("stream.status", scope, stream_id=stream_id, status=status.value)
        return stream

    def create_consumer_group(
        self, group: ConsumerGroup, scope: EventScope
    ) -> ConsumerGroup:
        self._require(scope, "events:subscribe")
        self._check(group, scope)
        topic = self.topics[self._key(group.topic, scope)]
        group.offsets = {partition: 0 for partition in range(topic.partitions)}
        group.checkpoints = dict(group.offsets)
        self.groups[self._key(group.name, scope)] = group
        return group

    def subscribe(self, subscription: Subscription, scope: EventScope) -> Subscription:
        self._require(scope, "events:subscribe")
        self._check(subscription, scope)
        group = self.groups[self._key(subscription.group, scope)]
        self._check(group, scope)
        self.subscriptions[subscription.id] = subscription
        self.subscribers.add((scope.tenant, scope.workspace, scope.actor))
        self._audit("subscription.create", scope, subscription_id=subscription.id)
        return subscription

    def add_route(self, route: RoutingRule, scope: EventScope) -> RoutingRule:
        self._require(scope, "events:manage")
        self._check(route, scope)
        if self._key(route.destination_topic, scope) not in self.topics:
            raise KeyError("Route destination topic does not exist.")
        self.routes[route.id] = route
        return route

    def publish(
        self,
        topic: str,
        payload: Any,
        scope: EventScope,
        *,
        schema: str,
        version: str,
        metadata: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        priority: int = 0,
        partition_key: str | None = None,
        transaction_id: str | None = None,
    ) -> Event:
        self._require(scope, "events:publish")
        topic_record = self.topics[self._key(topic, scope)]
        schema_record = self.schemas[(self._key(schema, scope), version)]
        body = json.dumps(payload, separators=(",", ":"), default=str).encode()
        if len(body) > self.max_payload_bytes:
            raise ValueError("Event payload exceeds configured size limit.")
        if self._contains_secret(payload) or self._contains_secret(headers or {}):
            raise ValueError("Secrets are not allowed in events.")
        schema_record.validate(payload)
        partition = (
            hash(partition_key or secrets.token_hex(8)) % topic_record.partitions
        )
        bucket = self.events[self._key(topic, scope)][partition]
        event = Event(
            secrets.token_hex(12),
            topic,
            payload,
            scope.tenant,
            scope.workspace,
            schema,
            version,
            partition,
            len(bucket),
            utcnow(),
            scope.actor,
            dict(metadata or {}),
            dict(headers or {}),
            priority,
            transaction_id,
        )
        bucket.append(event)
        self.publishers.add((scope.tenant, scope.workspace, scope.actor))
        self.metrics.increment("events_published_total")
        self._audit("event.publish", scope, event_id=event.id, topic=topic)
        return event

    def publish_batch(
        self, topic: str, payloads: list[Any], scope: EventScope, **options: Any
    ) -> list[Event]:
        if not payloads:
            return []
        return [self.publish(topic, payload, scope, **options) for payload in payloads]

    def publish_transaction(
        self, topic: str, payloads: list[Any], scope: EventScope, **options: Any
    ) -> list[Event]:
        transaction_id = secrets.token_hex(12)
        for payload in payloads:
            schema = self.schemas[
                (self._key(options["schema"], scope), options["version"])
            ]
            schema.validate(payload)
        return self.publish_batch(
            topic, payloads, scope, transaction_id=transaction_id, **options
        )

    def pull(
        self, subscription_id: str, scope: EventScope, *, limit: int = 100
    ) -> list[Event]:
        self._require(scope, "events:consume")
        subscription = self.subscriptions[subscription_id]
        self._check(subscription, scope)
        group = self.groups[self._key(subscription.group, scope)]
        candidates: list[Event] = []
        for key, partitions in self.events.items():
            topic = self.topics[key]
            if self._in_scope(topic, scope) and fnmatch.fnmatch(
                topic.name, subscription.topic_pattern
            ):
                for partition, bucket in enumerate(partitions):
                    offset = group.offsets.get(partition, 0)
                    candidates.extend(
                        event
                        for event in bucket[offset:]
                        if self._matches(event, subscription.filters)
                    )
        candidates.sort(
            key=lambda event: (
                -event.priority,
                event.published_at,
                event.partition,
                event.offset,
            )
        )
        result = candidates[: max(0, min(limit, 1000))]
        if group.delivery is DeliveryGuarantee.AT_MOST_ONCE:
            for event in result:
                group.offsets[event.partition] = max(
                    group.offsets.get(event.partition, 0), event.offset + 1
                )
        self.metrics.increment("events_consumed_total", len(result))
        self._update_lag(scope)
        return result

    def acknowledge(self, group_name: str, event: Event, scope: EventScope) -> None:
        self._require(scope, "events:consume")
        group = self.groups[self._key(group_name, scope)]
        self._check(group, scope)
        if event.tenant != scope.tenant or event.workspace != scope.workspace:
            raise PermissionError("Cannot acknowledge an event outside the scope.")
        group.offsets[event.partition] = max(
            group.offsets.get(event.partition, 0), event.offset + 1
        )
        self._update_lag(scope)

    def checkpoint(self, group_name: str, scope: EventScope) -> dict[int, int]:
        self._require(scope, "events:consume")
        group = self.groups[self._key(group_name, scope)]
        group.checkpoints = dict(group.offsets)
        self._audit("checkpoint.create", scope, group=group_name)
        return dict(group.checkpoints)

    def replay(
        self,
        group_name: str,
        scope: EventScope,
        *,
        offset: int | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        predicate: Callable[[Event], bool] | None = None,
    ) -> list[Event]:
        self._require(scope, "events:replay")
        group = self.groups[self._key(group_name, scope)]
        partitions = self.events[self._key(group.topic, scope)]
        replayed = [
            event
            for bucket in partitions
            for event in bucket
            if (offset is None or event.offset >= offset)
            and (start is None or event.published_at >= start)
            and (end is None or event.published_at <= end)
            and (predicate is None or predicate(event))
        ]
        for partition in group.offsets:
            matches = [e.offset for e in replayed if e.partition == partition]
            if matches:
                group.offsets[partition] = min(matches)
        self._audit("event.replay", scope, group=group_name, count=len(replayed))
        return replayed

    def fail_delivery(
        self,
        event: Event,
        group_name: str,
        scope: EventScope,
        reason: str,
        *,
        attempts: int,
    ) -> DeadLetter | None:
        group = self.groups[self._key(group_name, scope)]
        self._check(group, scope)
        self.metrics.increment("event_failures_total")
        if attempts <= group.retry_limit:
            self.metrics.increment("event_retries_total")
            return None
        item = DeadLetter(event, group_name, reason, attempts)
        self.dead_letters.append(item)
        self.metrics.increment("dead_letter_total")
        self._audit("event.dead_letter", scope, event_id=event.id, group=group_name)
        return item

    def cleanup(self, scope: EventScope, *, now: datetime | None = None) -> int:
        self._require(scope, "events:manage")
        moment = now or utcnow()
        removed = 0
        for key, topic in self.topics.items():
            if not self._in_scope(topic, scope):
                continue
            cutoff = moment - timedelta(seconds=topic.retention_seconds)
            for partition, bucket in enumerate(self.events[key]):
                retained = [event for event in bucket if event.published_at >= cutoff]
                removed += len(bucket) - len(retained)
                self.events[key][partition] = retained
        self._audit("retention.cleanup", scope, removed=removed)
        return removed

    def dashboard(self, scope: EventScope) -> dict[str, Any]:
        self._require(scope, "events:read")
        scoped_topics = [
            topic for topic in self.topics.values() if self._in_scope(topic, scope)
        ]
        scoped_groups = [
            group for group in self.groups.values() if self._in_scope(group, scope)
        ]
        return {
            "topics": [item.to_dict() for item in scoped_topics],
            "streams": [
                item.to_dict()
                for item in self.streams.values()
                if self._in_scope(item, scope)
            ],
            "publishers": sorted(
                actor
                for tenant, workspace, actor in self.publishers
                if (tenant, workspace) == (scope.tenant, scope.workspace)
            ),
            "subscribers": sorted(
                actor
                for tenant, workspace, actor in self.subscribers
                if (tenant, workspace) == (scope.tenant, scope.workspace)
            ),
            "consumer_groups": [item.to_dict() for item in scoped_groups],
            "dead_letter": [
                item.to_dict()
                for item in self.dead_letters
                if self._in_scope(item.event, scope)
            ],
            "replay": {
                "checkpoints": {item.name: item.checkpoints for item in scoped_groups}
            },
            "metrics": self.metrics.snapshot(),
        }

    @classmethod
    def _contains_secret(cls, value: Any) -> bool:
        if isinstance(value, dict):
            return any(
                cls.SECRET_KEYS.search(str(key)) or cls._contains_secret(item)
                for key, item in value.items()
            )
        if isinstance(value, (list, tuple)):
            return any(cls._contains_secret(item) for item in value)
        return False

    @staticmethod
    def _matches(event: Event, filters: dict[str, Any]) -> bool:
        return all(
            (event.payload.get(key) if isinstance(event.payload, dict) else None)
            == value
            for key, value in filters.items()
        )

    @staticmethod
    def _in_scope(record: Any, scope: EventScope) -> bool:
        return bool(
            record.tenant == scope.tenant and record.workspace == scope.workspace
        )

    def _update_lag(self, scope: EventScope) -> None:
        lag = 0
        for group in self.groups.values():
            if not self._in_scope(group, scope):
                continue
            for partition, bucket in enumerate(
                self.events[self._key(group.topic, scope)]
            ):
                lag += max(0, len(bucket) - group.offsets.get(partition, 0))
        self.metrics.set("consumer_lag", lag)


EnterpriseAIEventStreamingPlatform = EventStreamingPlatform
