# Marketplace Registry Foundation

## Scope

The Marketplace Registry Foundation is a **Reference Only** local index for
accepted publication snapshots. It is **Offline Only**: it does not open a
network connection, read a registry endpoint, start a worker, download an
artifact, install a package, resolve dependencies, create a lockfile, inspect
signatures, or perform authentication.

It is deliberately separate from the Sprint-1 `marketplace.registry`
`MarketplaceRegistry`. Existing callers retain that legacy public API. The new
foundation is available from `marketplace.registry_foundation`.

## Architecture

`ReferenceRegistryService` owns local, thread-safe entry and coordinate maps.
It accepts either a fully built immutable `RegistryEntry` or exactly one
explicit caller-provided accepted `PublicationSnapshot` through a
`RegistryPublicationAdapter`. It never scans, polls, or mutates a Publication
service.

Coordinates are `(publisher_id, package_id, version)`. Duplicate entry ids and
coordinates are rejected by default. Search, filtering, ordering, snapshots,
and statistics are derived locally and deterministically.

## Publication and Catalog Boundaries

`ReferenceRegistryPublicationAdapter` requires an explicitly injected
Publisher descriptor and rejects every status except `accepted`. The service
does not accept a publication service instance, so it cannot query hidden
publication state.

`ReferenceRegistryCatalogProjector` converts one Registry entry into a Package
Catalog descriptor. It does not retain or write to a catalog service; callers
choose whether to register that result elsewhere.

## Lifecycle and Events

Entries can be active, withdrawn, or deprecated. Repeating a request for an
already-target status is a no-op and does not create another event. Local
events use an increasing sequence number only—there are no timestamps,
EventBus subscriptions, or external side effects. `clear()` and `close()` are
idempotent. Operations after `close()` raise `RegistryClosedError`.

## Current Limitations

- No network or remote registry federation
- No package download
- No package installation
- No resolver, artifact storage, or lockfile creation
- No lockfile creation or version-selection algorithm
- No signatures, authentication, authorization, billing, or cloud integration
- No registry-to-catalog write path
