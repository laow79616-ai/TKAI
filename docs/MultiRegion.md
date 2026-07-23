# Multi-region Routing Foundation

`tkai.multiregion` is an optional, process-local region-selection layer. It
does not contact region endpoints or replace existing Runtime, ProviderManager,
AIClient, or Adaptive Routing behavior.

## Architecture

`RegionRegistry` stores immutable region metadata. `RegionTopology` classifies
regions as primary, secondary, backup, or disabled. `MultiRegionRouter` applies
an explicit `RegionPolicy` and ranks eligible caller-visible regions by preferred
order, topology role, priority, latency estimate, and region ID.

Breaker-open metadata, disabled topology entries, disabled regions, unhealthy
regions, missing capabilities, and policy exclusions are omitted. A fixed region
can be requested explicitly. Policy fallback only selects an enabled candidate;
there is no automatic network failover or traffic migration.

## Integration

Use `MultiRegionManager.select_region()` directly, or explicitly install the
Runtime or Policy adapter. EventBus events support local observability;
`DoctorService` and `tkai ai multiregion --json` provide read-only diagnostics.

## Known limitations

The foundation has no DNS, GeoIP, CDN, service mesh, Kubernetes, Consul, Redis
Cluster, leader election, gossip, active probes, or distributed synchronization.
Default behavior remains single-region and unchanged.
