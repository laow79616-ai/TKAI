# TKAI Marketplace V5 Publication Contracts Foundation

## Purpose

Publication Contracts Foundation models a local publication proposal lifecycle.
It is **Reference Only** and **Offline Only**: it stores immutable descriptions
in one explicit service instance and never transfers a package artifact.

## Architecture and module boundaries

```text
Publisher + PackageManifest + Policy
               |
               v
PublicationRequest -> Validator -> PublicationLifecycle -> Snapshot
               |
               +-> ReferencePublicationService (local memory only)
```

The `marketplace.publication` namespace consumes Publisher and Package Catalog
descriptors through explicit inputs. It does not modify `marketplace.publisher`,
`marketplace.package_catalog`, the Sprint-1 Marketplace Registry, or any
Platform layer.

## Publication models

`PublicationId`, `PublicationRequest`, `PublicationManifest`,
`PublicationMetadata`, `PublicationResult`, `PublicationIssue`,
`PublicationSnapshot`, `PublicationStatus`, and `PublicationDecision` are frozen
and JSON-safe. All metadata mappings are defensively copied. Time is never read
implicitly; this reference foundation does not create timestamps.

## Lifecycle

The local lifecycle permits:

- draft → submitted
- submitted → validating
- validating → accepted or rejected
- draft or submitted → withdrawn
- rejected → submitted

All other transitions raise `PublicationStateError` and leave the original
snapshot unchanged.

## Policy and validation

`PublicationPolicy` and `PublicationPolicyRule` declare local structural rules
for publisher tier, prerelease versions, dependencies, compatibility targets,
duplicate coordinates, tag count, and metadata count. They do not authenticate,
authorize, call `PublisherTrust`, call `PublisherVerification`, or enforce
Enterprise permissions.

`PublicationValidator`, `PublicationPolicyEvaluator`, and
`PublicationDuplicateChecker` are Protocols only. `ReferencePublicationValidator`
checks required values, package structure, transitions, and local policy with
deterministic issue ordering.

## Duplicate semantics

A publication coordinate is `(publisher_id, package_id, version)`. The default
policy rejects a duplicate coordinate; it never silently replaces an existing
local snapshot.

## Reference service

`ReferencePublicationService` supports submit, validate, accept, reject,
withdraw, get, list, snapshot, clear, and close. It is thread-safe, has no
background worker, isolates instances, and provides idempotent close. It does
not automatically register an accepted package in Marketplace or Catalog state.

## Explicit non-goals and limitations

- No artifact upload, file storage, or package download.
- No package installation.
- No remote registry, database, network transport, resolver, or lockfile.
- No authentication, account lookup, real verification, signature enforcement,
  permission grant, billing, or Cloud integration.
- No Runtime, SDK, Studio, Enterprise, or Cloud modification.

## Next foundation boundary

Registry, resolver, installer, and verification-enforcement work remain outside
this Sprint and require a separate explicit design phase.
