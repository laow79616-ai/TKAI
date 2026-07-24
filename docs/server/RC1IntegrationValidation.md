# Marketplace Server V6 RC-1 Integration Validation

## Validation scope

RC-1 validates the local integration of Registry, Publisher, Package, Version,
Search, Statistics, and Health. Every scenario uses explicitly constructed
models, explicitly injected reference storage, and pure-memory reference
services. No domain discovers, probes, indexes, or mutates another domain.

## Scenarios and results

- Registry → Publisher → Package → Version validates descriptive relationship
  values only; no service-to-service lookup occurs.
- Unified Search receives caller-supplied Package and Version search entries.
- Statistics receives caller-supplied Registry, Publisher, Package, and Version
  source records.
- Health receives caller-supplied checks and results for each domain; it runs no
  probe.
- Historical snapshots are ordered, immutable, JSON-safe, and unaffected by
  later clear operations.
- Event sequences are local, monotonic, and close emits exactly one event.
- Multiple instances remain isolated; bounded eight-worker, 32-operation
  validation does not use sleep or network access.
- Failure isolation verifies rejected Registry duplicates, rejected Statistics
  duplicates, and missing Health checks do not affect unrelated foundations.

## Lifecycle and compatibility results

All foundations reject mutations after close while retaining final snapshot,
event, and statistics/counter access according to their public contracts.
Registry was corrected to retain final snapshot and statistics reads after
close; the final snapshot no longer creates an extra event. Search now exposes
its existing immutable event sequence through a read-only `events()` method,
matching the other event-bearing foundations.

Runtime, SDK, Studio, Enterprise, Cloud, and Marketplace Foundation import
compatibility remains intact. Package documentation inclusion is checked against
`MANIFEST.in` and `pyproject.toml`.

## Known limitations

The Server remains Reference Only, Offline Only, and Pure Memory. It has no
HTTP/REST API, network, database, Redis, authentication, background worker,
scheduler, search engine, monitoring probe, filesystem persistence, or cloud
deployment behavior.

## Release blockers and recommendation

**Release blockers:** None in the RC-1 integration scope.

**RC-2 recommendation:** READY for Performance and Reliability Validation.
This document does not start RC-2.
