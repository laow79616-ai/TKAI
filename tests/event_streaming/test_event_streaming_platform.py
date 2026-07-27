from datetime import timedelta

import pytest

from event_streaming import (
    ConsumerGroup,
    DeliveryGuarantee,
    EventSchema,
    EventScope,
    EventStream,
    EventStreamingAPI,
    EventStreamingPlatform,
    StreamStatus,
    Subscription,
    Topic,
    utcnow,
)


@pytest.fixture
def system():
    platform = EventStreamingPlatform(max_payload_bytes=1024)
    scope = EventScope("tenant-a", "workspace-a", "alice", frozenset({"events:admin"}))
    platform.create_topic(
        Topic("ai.events", scope.tenant, scope.workspace, partitions=2), scope
    )
    platform.register_schema(
        EventSchema(
            "ai-event",
            "1",
            scope.tenant,
            scope.workspace,
            frozenset({"type"}),
            {"type": "string"},
        ),
        scope,
    )
    platform.create_stream(
        EventStream(
            "s1",
            "AI Events",
            "Enterprise events",
            scope.tenant,
            scope.workspace,
            "ai.events",
            "ai-event",
            "1",
        ),
        scope,
    )
    platform.set_stream_status("s1", StreamStatus.ACTIVE, scope)
    platform.create_consumer_group(
        ConsumerGroup("workers", "ai.events", scope.tenant, scope.workspace), scope
    )
    platform.subscribe(
        Subscription("sub1", "ai.*", "workers", scope.tenant, scope.workspace), scope
    )
    return platform, scope


def test_topics_stream_lifecycle_and_schema(system):
    platform, scope = system
    assert platform.dashboard(scope)["streams"][0]["status"] == "active"
    platform.set_stream_status("s1", StreamStatus.PAUSED, scope)
    assert platform.streams["s1"].status is StreamStatus.PAUSED
    with pytest.raises(ValueError):
        platform.publish("ai.events", {}, scope, schema="ai-event", version="1")


def test_publish_subscribe_ack_checkpoint_and_replay(system):
    platform, scope = system
    events = platform.publish_transaction(
        "ai.events",
        [{"type": "started"}, {"type": "finished"}],
        scope,
        schema="ai-event",
        version="1",
        partition_key="job",
    )
    pulled = platform.pull("sub1", scope)
    assert [event.id for event in pulled] == [event.id for event in events]
    platform.acknowledge("workers", pulled[0], scope)
    checkpoint = platform.checkpoint("workers", scope)
    assert checkpoint[pulled[0].partition] == 1
    assert len(platform.replay("workers", scope, offset=0)) == 2


def test_delivery_dead_letter_retention_and_metrics(system):
    platform, scope = system
    event = platform.publish(
        "ai.events", {"type": "failed"}, scope, schema="ai-event", version="1"
    )
    assert platform.fail_delivery(event, "workers", scope, "boom", attempts=1) is None
    dead = platform.fail_delivery(event, "workers", scope, "boom", attempts=4)
    assert dead is not None
    platform.topics[platform._key("ai.events", scope)].retention_seconds = 1
    event.published_at = utcnow() - timedelta(seconds=2)
    assert platform.cleanup(scope) == 1
    metrics = platform.metrics.snapshot()
    assert metrics["event_retries_total"] == 1
    assert metrics["dead_letter_total"] == 1


def test_security_isolation_payload_and_secrets(system):
    platform, scope = system
    other = EventScope(
        "tenant-b", "workspace-a", "mallory", frozenset({"events:admin"})
    )
    with pytest.raises(KeyError):
        platform.publish(
            "ai.events", {"type": "x"}, other, schema="ai-event", version="1"
        )
    with pytest.raises(ValueError, match="Secrets"):
        platform.publish(
            "ai.events",
            {"type": "x", "api_key": "bad"},
            scope,
            schema="ai-event",
            version="1",
        )
    with pytest.raises(ValueError, match="size"):
        platform.publish(
            "ai.events",
            {"type": "x", "data": "x" * 2000},
            scope,
            schema="ai-event",
            version="1",
        )


def test_api_dashboard_and_at_most_once(system):
    platform, scope = system
    platform.groups[
        platform._key("workers", scope)
    ].delivery = DeliveryGuarantee.AT_MOST_ONCE
    api = EventStreamingAPI(platform)
    api.post(
        "/publish",
        scope,
        {
            "topic": "ai.events",
            "payload": {"type": "x"},
            "schema": "ai-event",
            "version": "1",
        },
    )
    assert len(api.post("/subscribe", scope, {"subscription_id": "sub1"})) == 1
    assert api.post("/subscribe", scope, {"subscription_id": "sub1"}) == []
    dashboard = platform.dashboard(scope)
    assert dashboard["topics"] and dashboard["publishers"] and dashboard["subscribers"]
    assert set(EventStreamingAPI.ROUTES) == {
        "/event-streams",
        "/topics",
        "/publish",
        "/subscribe",
        "/replay",
        "/checkpoints",
    }
