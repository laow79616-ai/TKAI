# TKAI Platform 1.0 Release Notes

## Release summary

Platform 1.0.0 establishes a documented general-availability baseline for
Runtime 1.3.0, SDK 2.0, and Studio 2.1. The release preserves Runtime public
APIs and keeps SDK and Studio additive.

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

## Compatibility and limitations

There are no Platform 1.0 breaking changes to established Runtime APIs. Known
limitations include local-memory reference stores, no production Studio
authentication/persistence/WebSocket, no real Provider or Agent Chat transport,
no automatic failover takeover, no distributed state synchronization, and no
bundled frontend build output. See [Platform.md](Platform.md) for the full
layering model.
