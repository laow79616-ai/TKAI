# TKAI 2.0 Memory SDK

## Architecture

`tkai.sdk.memory` is an additive, vendor-neutral contract layer. It defines
memory records, queries, result snapshots, namespace/session identifiers,
lifecycle values, policies, hooks, a registry, and a factory. It does not
replace `tkai.sdk.memory` from the earlier SDK architecture or alter V1.x
runtime memory behaviour.

## Reference memory

`ReferenceMemory` is a deterministic in-process implementation for tests,
examples, and SDK smoke checks. It is thread-safe, bounded, namespace and
session aware, uses lazy local TTL expiry, provides store/get/delete/list/clear
and snapshot operations, and returns defensive record copies. It starts no
threads, writes no disk data, reads no environment variables, and contacts no
network service.

## Lifecycle, registry, and factory

Callers explicitly construct and close reference memory. `MemoryRegistry`
registers existing implementations without choosing a default; `MemoryFactory`
creates only builders registered by the application. Both are thread-safe and
return results in stable name order.

## Policies and hooks

Eviction, TTL, capacity, overwrite, snapshot, and retention are extension
protocols. Store/query/error and telemetry hooks are also protocols only. No
policy or telemetry behaviour is enabled implicitly.

## Current limitations

This sprint deliberately excludes Redis, vector databases, embeddings,
semantic search, RAG, disk persistence, and remote storage. Reference memory
is not a production persistence implementation.
