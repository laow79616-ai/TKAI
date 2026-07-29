# Operations Guide

Register descriptors without activating them. Validate grants and dependencies,
then use `CapabilityLoader` to load in dependency order and activate explicitly.
Monitor readiness, liveness, diagnostics, heartbeats, error counts, latency,
load and activation counts, and availability through the dashboard or GET-only
API.

Pause before planned intervention. Disable unhealthy capabilities when
dependents permit it. Deprecate with replacement and retirement metadata before
retiring. A retired capability cannot be reactivated.
