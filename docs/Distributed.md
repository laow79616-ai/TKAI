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

## Active health probes

The optional `BackendHealthChecker` runs explicit active probes for
`LocalBackend`/`LocalMemoryBackend` and `RedisBackend`. It caches immutable
`BackendHealthSnapshot` values with `healthy`, `degraded`, or `unhealthy`
status, the last probe timestamp, a safe error type, and a failure count.
Existing `backend.health()` methods remain passive lifecycle checks and do not
start probing.

Use `checker.probe()` or `await checker.aprobe()` for one check. `start()`
enables a single periodic daemon worker; `stop()`/`close()` stops and joins it
without closing the caller-owned backend. `HealthProbeConfig` controls interval,
cooperative timeout, immediate bounded retry count, and status thresholds.
`BackendFactory.create_health_checker()` derives these settings from
`BackendConfig`. Probes are opt-in and never alter ProviderManager or Runtime
default behavior.

## Automatic failover

`FailoverManager` is an explicit opt-in layer above health probes. It uses a
configured primary and a secondary backend, defaulting the secondary to a new
`LocalMemoryBackend`. Reaching `FailoverConfig.failure_threshold` consecutive
non-healthy primary probes activates the secondary. While the secondary is
active, reaching `recovery_threshold` healthy primary probes changes the state
to `primary_recovered`; callers must invoke `manual_failback()` to reactivate
the primary. This avoids automatic switch-back flapping.

The state machine is `primary_active`, `secondary_active`, and
`primary_recovered`. Its snapshots include priority, counters, health, metrics,
and transition time. Optional EventBus notifications are published for failover,
recovery detection, and failback, but subscriber errors are isolated. Starting
the manager enables periodic checks; stopping it releases only its worker and
never closes caller-owned backends.

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
