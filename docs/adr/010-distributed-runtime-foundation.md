# ADR 010: Distributed Runtime Foundation

## Decision

Provide a backend protocol and a default LocalBackend, coordinated only by an
explicit `DistributedCoordinator` and adapters.

## Rationale

The backend boundary permits future external implementations without adding
network dependencies or changing stable Provider Runtime APIs. Local
membership, locks, and cooperative heartbeat make lifecycle behaviour testable
offline. Explicit adapters preserve existing default behaviour.

## Consequences

V1.2 has no leader election, gossip, remote backend, distributed persistence,
or automatic service takeover. Applications must construct and start a
coordinator deliberately.
