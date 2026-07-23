# Distributed Runtime Foundation

`tkai.distributed` is an optional Distributed Runtime foundation. Its default
`LocalBackend` (also exported as `LocalMemoryBackend`) is thread-safe,
in-memory, synchronous, and supports async wrapper methods. It makes no
network calls and is not enabled by ProviderManager, AIClient, or Provider
Runtime.

## Redis backend

`RedisBackend` is an explicit, optional backend. Install its dependency with
`pip install tkai[redis]`, then construct it through `BackendFactory` or
`create_backend(BackendConfig(kind="redis"))`. Redis is imported lazily, so
using the default local backend never requires it. The backend has explicit
`connect`/`disconnect` lifecycle methods, bounded immediate reconnect attempts,
configurable connection timeout, JSON-only values, namespaced keys, and async
wrappers for its synchronous client.

Applications may inject a compatible Redis client for tests or client ownership.
Injected clients are never closed by TKAI; clients created internally are closed
on disconnect. The existing `subscribe` callback contract remains in-process;
remote Redis pub/sub consumer loops are deliberately not started implicitly.

## Architecture

`DistributedCoordinator` owns an explicit backend, local `Membership`, a
cooperative `Heartbeat`, local locks, and a registry of application-supplied
health/cache/retry/rate-limit/plugin resources. Registering a resource only
retains a diagnostic reference; it never starts or changes that service.

## Membership, heartbeat, and locks

Nodes contain an id, hostname, UTC timestamps, capabilities, and local status.
Membership registration, heartbeat, removal, and optional expiry simulation are
thread-safe. Heartbeat has no background thread: callers explicitly call
`start()`, `beat()`, and `stop()`. `LocalLock` uses the selected backend and
supports acquire, release, renew, and safe snapshots.

## Runtime and Policy Engine integration

`DistributedRuntimeAdapter` starts or stops a caller-supplied coordinator; it
does not modify the existing Runtime public API. `DistributedPolicyAdapter`
only places the coordinator into an explicit PolicyContext. It does not start
the coordinator or affect default request routing.

## Observability, Doctor, and CLI

Node, heartbeat, lock, and coordinator lifecycle events reuse EventBus. Doctor
inspects only a supplied coordinator. `tkai ai distributed` renders backend,
coordinator, nodes, heartbeat, and resource metadata in text or JSON.

## Known limitations

This foundation has no Etcd, Consul, ZooKeeper, gossip protocol, leader
election, remote Redis pub/sub consumer loop, atomic Redis lock compare/delete,
multi-region routing, distributed lease semantics, or automatic ProviderManager
takeover. The default remains single-process and in-memory.
