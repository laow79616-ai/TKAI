# Marketplace Server V6 Architecture Review

## Review scope

This review covers the Server Architecture contracts and the Registry,
Publisher, Package, Version, Search, Statistics, and Health foundations. It
reviews public exports, dependency direction, immutable models, lifecycle and
event behavior, snapshots, thread safety, failure isolation, packaging, and
documentation. It does not add a business domain or production capability.

## Architectural principles

All reviewed foundations remain Reference Only, Offline Only, Pure Memory, and
Contract First. Models are immutable; services receive explicit storage
dependencies; reference storage is per instance and thread-safe; ordering and
event sequences are deterministic. No reviewed foundation creates a hidden
service, global singleton, worker, scheduler, network client, database, or
filesystem persistence.

## Dependency direction and domain boundaries

Each packaged domain uses Models → Storage Protocol → Reference Storage, with
the Reference Service depending on the protocol rather than another domain's
implementation. Static import review found no direct cross-domain Server
service imports in Registry, Publisher, Package, Version, Search, Statistics,
or Health.

Package and Version retain publisher/package references as explicit descriptor
values only. Unified Search accepts caller-supplied `SearchEntry` values;
Statistics accepts caller-supplied sources and records; Health accepts
caller-supplied checks and results. None discovers or reads another domain's
storage.

## Public API and model consistency

All reviewed domains expose a stable tuple `__all__`; exports contain public
models, protocol, reference storage, reference service, and domain errors—not
locks, containers, or private helpers. Models use frozen dataclasses and tuples,
frozensets, or defensively copied mappings. Snapshots and events are JSON-safe,
ordered deterministically, and do not depend on system time, random values, or
environment state.

Identifier validation stays domain-specific while following the same principle:
identifiers are explicit, non-empty, deterministic, and never implicitly
generated. No shared identifier hierarchy was introduced because it would add
coupling without changing an actual inconsistency.

## Lifecycle, events, snapshots, and clear semantics

Stateful Registry, Publisher, Package, Version, Statistics, and Health
transitions emit one sequence event only for an actual state change. Repeated
target-state operations are idempotent where the respective domain supports
them. Failed duplicate or invalid transitions occur before event recording.

Clear removes active local reference data but does not rewrite prior snapshots.
Statistics and Health retain their monotonic event history across clear.
Search maintains its explicitly documented latest-result behavior. All
foundations make final snapshots, counters/statistics, and events available
after idempotent close while rejecting mutations. Read behavior beyond these
final views remains domain-specific and is documented by each foundation.

## Thread safety and failure isolation

Reference storage forms snapshots while holding its local lock and returns
immutable values only. Sequence allocation and event recording are serialized
by each service instance. Bounded eight-worker, 32-operation checks demonstrate
no cross-instance contamination. Duplicate writes, invalid transitions, missing
objects, and rejected batches do not alter existing state or other instances.

## Error, packaging, and documentation review

Each foundation retains a domain-local error hierarchy. Value-object validation
may raise `ValueError` where its public construction contract already specifies
that behavior; service/storage failures use domain errors. Error messages
contain neither credentials nor local paths.

`MANIFEST.in` and `pyproject.toml` include Architecture, Foundation, and
Service documentation for Registry, Publisher, Package, Version, Search,
Statistics, and Health. Documentation contains no local absolute paths and
does not claim production monitoring, storage, or network capabilities.

## Findings

| ID | Severity | Module | Description | Resolution | Test coverage | Status |
| --- | --- | --- | --- | --- | --- | --- |
| SRV-AR-001 | Medium | `server.health` | The concrete Health foundation lacked an explicit stable export list. | Added a deterministic `__all__` containing only public models, errors, protocol, and reference implementations. | `test_public_domain_imports_are_explicit_and_stable` | Resolved |
| SRV-AR-002 | Low | Unified Search | A Search snapshot records results only after an explicit query, rather than copying injected entries into a result view. | Retained the documented explicit-query contract; the review test invokes `search()` before asserting historical result snapshots. | `test_snapshots_are_historical_json_safe_and_finally_readable` | Accepted |
| SRV-AR-003 | Accepted Design Difference | `server.health` | Health remains a compatibility-preserving module file rather than a same-named package because `server/health.py` was a Sprint-1 public import path. | Retained the module structure and extended it compatibly; a same-named package could shadow existing imports. | import and legacy Server architecture tests | Accepted |

No Critical or High findings remain. No Medium finding blocks RC-1.

## Remaining limitations and release recommendation

The Server remains a local reference architecture: no HTTP, REST, GraphQL,
network, database, Redis, filesystem persistence, search engine, exporter,
automatic monitoring, background worker, scheduler, authentication,
authorization, artifact transport, or release pipeline exists.

**Release blockers:** None for the reviewed Foundation scope.

**RC-1 recommendation:** READY for Integration Validation, subject to normal
release acceptance. This review does not begin RC-1.
