# TikTok Runtime Manager

## Architecture

The Runtime Manager is the local control plane for TKAI TikTok services. It uses
ports for existing Workflow, Automation, Metrics, Observability, Security, Audit,
Event Streaming, and Local Runtime implementations. It does not replace them or
connect directly to TikTok.

## Lifecycle

Instances move through Initializing, Starting, Ready, Running, Paused,
Recovering, Stopping, Stopped, Archived, and Deleted using an explicit transition
table. Concurrent lifecycle operations are rejected by a bounded runtime lock.

## Startup

Startup validates service configuration and dependencies, topologically orders
services, starts each through its registered port, validates health, and rolls
back already-started services in reverse order after a failure.

## Shutdown

Shutdown reverses dependency order. Each port drains workers and queues, stops
the service, and cleans up browser, device, lease, and PID references. The
manager then clears its process and worker registries.

## Registry and supervision

The registry records service capabilities, dependencies, version, health, and
heartbeat. Supervision detects stale running services and applies bounded restart
policies with attempt limits, cooldown configuration, and optional approval.

## Recovery

Recovery performs cleanup, validation, restart, and health validation. It stops
immediately when an unresolved TikTok restriction or challenge is recorded.
Checkpoint-aware modules should resume through their existing service ports.

## Health, telemetry, and statistics

Runtime, service, registry, startup, shutdown, and composite health are exposed
alongside Prometheus metrics, availability, restart rate, recovery success,
startup/shutdown duration, failure distribution, and utilization. CPU and memory
remain host-observability concerns and are deliberately represented as optional
values rather than duplicated collectors.

## Security

Every operation enforces tenant/workspace isolation and RBAC. Mutating runtime
operations are bounded. Approval references are required by manual policies.
Metadata and audit events reject secret-bearing fields; integrations should pass
encrypted references only.

## Operations guide

Register dependency services before dependants, attach production ports, call
`start`, send heartbeats, supervise on a bounded timer, and call `stop` during
local shutdown. Investigate blocked recovery instead of retrying restrictions.

## Windows local guide

Run the manager inside the existing TKAI local-runtime process. Store the
workspace below the configured local TKAI data directory, use process-reference
IDs rather than raw command lines, and invoke graceful shutdown before Windows
logoff or service termination.
