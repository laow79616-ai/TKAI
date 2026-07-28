# Enterprise TikTok Browser Cluster

## Architecture

The cluster is a local orchestration layer over the existing Browser Runtime. Narrow
ports reference Browser Runtime and Risk Control; Account, Proxy, Workflow, Operations,
metrics, audit, and security remain owned by their existing modules. No live TikTok
access is required.

## Lifecycle and scheduling

Clusters move through initializing, ready, running, scaling, paused, recovering,
maintenance, archived, and deleted states using validated transitions. A stable
priority heap provides bounded, workspace-scoped scheduling. Account and workspace
limits prevent monopolization; equal-priority work remains FIFO.

## Resource allocation

CPU, memory, browser slots, total browsers, per-workspace browsers, per-account
browsers, and parallel launches are hard bounds. Nodes are selected by available
slots and lowest current load. Stopping an instance releases reservations.

## Recovery

Recovery uses session references and is limited by attempts, backoff, cooldown, and
optional manual approval. It stops and pauses an instance whenever Risk Control
reports an unresolved TikTok restriction or challenge. The cluster does not bypass
CAPTCHAs, restrictions, or platform security.

## Telemetry and statistics

Prometheus-style metrics cover clusters, nodes, instances, running browsers, queues,
failures, recoveries, CPU, memory, and launch latency. The dashboard provides cluster,
node, instance, queue, resource, health, recovery, telemetry, and statistics views.

## Security

Every operation applies tenant/workspace isolation and RBAC. Audit records contain
references, never credentials. Secret- or token-like metadata is rejected from cluster
metadata. Resource bounds limit local impact.

## Operations and Windows local guide

Use a loopback-only deployment and configure node capacity below physical Windows
limits. Register a node, send periodic heartbeats, enqueue Browser Runtime references,
and monitor health score plus queue depth. Pause or enter maintenance before changing
capacity. Investigate manual-review recovery records before approving another attempt.
Use the existing local-runtime PowerShell scripts for platform start and stop.
