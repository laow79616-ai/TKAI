# TKAI V3.0 Enterprise Release Notes

## Release summary

TKAI V3.0 establishes a unified `3.0.0` general-availability baseline for the
Runtime, SDK, Agent Runtime, Plugin Marketplace, Enterprise Platform, Cloud
Native deployment, AI Studio, Enterprise Marketplace, API, and Dashboard. This
release focuses on quality, consistency, documentation, and packaging; it adds
no product behavior. See [the complete V3.0 release guide](release/V3.0.md).

## Runtime 1.3.0

Runtime includes the provider framework, workflow controls, local diagnostics,
configuration and credential foundations, optional distributed/local backends,
health probes, failover foundations, service discovery, telemetry abstraction,
and adaptive scheduler. Optional integrations remain explicit and local-first.

## SDK 2.0

SDK 2.0 provides explicit Agent, Provider, Memory, Workflow, Tool, and Plugin
contracts plus deterministic reference implementations. It composes on Runtime
without changing V1.x Runtime defaults.

## Studio 2.1

Studio provides the independent backend foundation, frozen local REST contract,
React frontend foundation, reference Workflow Designer, Execution Monitor, and
Agent Chat contracts. Studio uses public SDK boundaries and adds no hidden
Provider, Runtime, network, or credential behavior.

## Enterprise 3.0

Enterprise provides offline reference contracts for identity, organization,
tenant boundaries, authorization descriptors, audit records, and license
entitlements. These foundations are packaged with `tkai` but remain explicit:
they do not add authentication, persistence, authorization or feature
enforcement, billing, cloud services, or automatic integration into Runtime,
SDK, Studio, or the frozen REST API.

## Compatibility and limitations

There are no Platform 1.0 breaking changes to established Runtime APIs. Known
limitations include local-memory reference stores, no production Studio
authentication/persistence/WebSocket, no real Provider or Agent Chat transport,
no automatic failover takeover, no distributed state synchronization, and no
bundled frontend build output. Enterprise likewise has no authentication,
persistence, audit export, license activation, or enforcement. See
[Platform.md](Platform.md) for the full layering model.
