# Enterprise AI Event Streaming Platform

## Architecture

The platform is a tenant- and workspace-scoped control plane and reference broker. Topics own partitioned append-only event logs; streams bind topics to versioned schemas; consumer groups own offsets and checkpoints. The framework-neutral API facade exposes `/event-streams`, `/topics`, `/publish`, `/subscribe`, `/replay`, and `/checkpoints`.

## Topics and streams

Topics support bounded retention, partitions, archive configuration, a replication interface, and compaction configuration. Streams carry ID, name, description, tenant, workspace, topic, schema, version, lifecycle status, and metadata. Lifecycle transitions are validated across Draft, Active, Paused, Archived, and Deleted.

## Delivery

Publishers can send single events, batches, or prevalidated transactions with metadata, headers, priority, and stable partition keys. Pull and HTTPS push subscriptions are modeled with consumer groups. At-least-once delivery advances offsets on acknowledgement; at-most-once delivery advances them on read. Groups configure ordering, retry limits, timeouts, and dead-letter handling.

## Replay and retention

Checkpoints capture group offsets. Replay supports offsets, time windows, and selective predicates. TTL cleanup is explicit and auditable. Archive and compaction are storage-adapter interfaces represented on topics; production adapters can implement durable archive and key compaction without changing the control plane.

## Schemas

The registry stores named versions, validates required fields and primitive types, and enforces none, backward, forward, or full compatibility modes. Backward/full evolution cannot remove previously required fields.

## Security

Every operation applies tenant and workspace isolation plus RBAC. Payloads have configurable bounded sizes, schemas are validated before append, and secret-like keys are rejected recursively. Audit entries exclude secret-bearing metadata. Push destinations must use HTTPS.

## Observability and dashboard

The dashboard reports topics, streams, publishers, subscribers, consumer groups, dead letters, replay checkpoints, and metrics. Prometheus output includes `events_published_total`, `events_consumed_total`, `event_failures_total`, `event_retries_total`, `dead_letter_total`, `consumer_lag`, and `stream_latency_seconds`.
