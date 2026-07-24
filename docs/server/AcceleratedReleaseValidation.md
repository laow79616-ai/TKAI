# Marketplace Server V6 Accelerated Release Validation

## Scope and integration

This validation consolidates the completed Foundation, Architecture Review, and
RC-1 integration work for Registry, Publisher, Package, Version, Search,
Statistics, and Health. All flows use explicit local models, injected
reference storage, and isolated pure-memory services. No domain discovers or
mutates another service.

## Reliability and concurrency

Release validation repeats a compact Reference workflow for ten deterministic
rounds. It verifies snapshot, counter, and close stability without sleep or
random ordering. Existing Foundation and RC-1 suites provide bounded
eight-worker / 32-operation checks for concurrent local writes and snapshots.
No worker, scheduler, or network operation is started.

## Benchmark summary

`benchmarks.server` contains deterministic reference scenarios for Registry
create/list/search; Publisher, Package, and Version create/search; Unified
Search; Statistics record/query/aggregate; and Health update/snapshot. The
module exposes `reports()` with human-readable Markdown and machine-readable
JSON for every scenario. Results are regression references only: no absolute
performance threshold or cross-machine comparison is made.

## Packaging and fresh-install validation

The release validation produced `tkai-1.3.0-py3-none-any.whl` and
`tkai-1.3.0.tar.gz` with existing offline setuptools/PIP tooling. The standard
`python -m build` entry point was unavailable in this environment, so no
dependency was installed. Wheel and source distribution contents were audited
for Server modules, Server documents, LICENSE, metadata, caches, temporary
paths, and credentials.

The wheel installed into a fresh isolated environment and completed the minimal
Reference workflow. The source distribution completed the same workflow in an
isolated environment provisioned with the standard `setuptools` build backend.
A completely empty offline environment cannot build an sdist without that
declared build backend; this is an environment prerequisite, not a runtime
dependency of the Server. `twine` was unavailable, so metadata was checked with
the wheel metadata and standard archive inspection rather than adding a new
tool.

The workflow imports every Server Foundation and exercises explicit Publisher
→ Package → Version → SearchEntry → StatisticsRecord → HealthResult state
before reading snapshots and closing services.

## Version decision

Marketplace Server has no independent package version. It is released with the
existing `tkai` package version `1.3.0`; no second version source was created.

## Known limitations

Marketplace Server is Reference Only, Offline Only, and Pure Memory. It has no
HTTP API, network, database, Redis, filesystem persistence, authentication,
background worker, monitoring probe, container integration, or deployment
infrastructure.

## Release blockers and recommendation

**Release blockers:** None after the completed validation steps.

**GA baseline recommendation:** Ready for release review, subject to artifact
validation in the target release environment. This document starts no HTTP API
or Dashboard work.
