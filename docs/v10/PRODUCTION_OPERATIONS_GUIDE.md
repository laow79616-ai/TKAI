# V10 Production Operations Guide

Before rollout, verify the source commit, manifests, SHA-256 checksums, archive
contents, OpenAPI inventory, environment prerequisites, backups, and existing
V6-V9 smoke tests. Deploy through the established operator-controlled process.
Watch readiness, liveness, audit correlation, mesh health, latency, and error
metrics. Pause or roll back through existing deployment procedures; V10 itself
does not execute recovery, rollback, migration, or service-control actions.
