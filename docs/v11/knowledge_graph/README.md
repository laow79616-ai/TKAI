# Autonomous Knowledge Graph

TKAI V11 exposes a unified, deterministic metadata graph for ecosystem references.
It is local-first, immutable, explainable, advisory, and read-only. Nodes and edges
describe references only; they never invoke the referenced component.

The graph covers framework, capability, module, service, extension, configuration,
runtime, API, dashboard, AI Studio, policy, constraint, trust, integrity,
compatibility, knowledge, reasoning, decision, planning, operations, and recovery
metadata.

## Safety boundary

The graph has no execution, mutation, traversal, optimization, scheduling,
deployment, recovery, browser, TikTok, resource-allocation, or planning actions.
It performs no network access and does not read or write runtime storage.

## Compatibility

Lineage metadata retains V6 through V11 compatibility. Existing V6, V7, V8, V9,
V10, and V11 Intelligence API routes are unchanged. The V11 graph is additive at
`/v11/graph`.
