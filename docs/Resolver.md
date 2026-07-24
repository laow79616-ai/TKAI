# Marketplace Dependency Resolver Foundation

## Purpose

This **Reference Only** and **Offline Only** resolver transforms a caller-owned
Registry Foundation snapshot into a deterministic dependency graph and immutable
resolution result. Its explicit flow is Registry Snapshot to Resolution Source,
then Dependency Graph, then Resolution Result. It has no service singleton,
worker, or external state.

## Models and candidate selection

Coordinates identify a publisher, package, and explicit `PackageVersion`.
Requirements support an optional publisher, exact `==1.2.3`, limited compatible
`>=1.2.0,<2.0.0`, or `any` version rules. The default strategy sorts candidates
by publisher, package, and version. No remote version lookup occurs.

## Graph and diagnostics

The immutable graph exposes stable roots, leaves, dependency and dependent
queries, cycles, and dependency-first order. Missing roots, missing dependencies,
optional skips, cycles, duplicate declarations, version conflicts, and ambiguity
yield deterministic issues and explanations. Cyclic results do not claim a
successful dependency order.

## Boundaries and safety

`ReferenceRegistryResolutionSource` copies a supplied `RegistrySnapshot` into
a stable candidate view. The resolver never modifies Registry, Catalog, or
Publication state. It is thread-safe, stores only the last result, and supports
idempotent `clear()` and `close()` operations.

Target versions are explicit request data. There is no environment version
detection and compatibility declarations are descriptive only.

## Explicit non-goals

- No network, No download, and No installation
- No lockfile, remote registry, artifact handling, or filesystem scan
- No environment version detection or package mutation
- No automatic registry update or signature verification
- No resolver-to-installer integration, authentication, authorization, billing,
  or cloud behavior
