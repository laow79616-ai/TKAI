# Marketplace V5 RC-3 Packaging & Release Validation

Baseline: `970fa11` (Marketplace RC-2 performance and reliability validation).

## Release checklist

- Version and package metadata: reviewed against the single `tkai` 1.3.0
  distribution version.
- Packaging: wheel and sdist built using the local setuptools build backend.
- Fresh install: validated from local wheel and sdist in clean temporary
  environments, with Marketplace imports and the reference workflow only.
- Distribution audit: confirms Marketplace sources, documentation, release
  notes, and benchmark descriptors are packaged without caches, credentials,
  local paths, or test output.
- Compatibility: Marketplace remains additive and does not modify Runtime, SDK,
  Studio, Enterprise, or Cloud public APIs.

## Known limitations

Marketplace remains entirely offline and reference-only. It has no remote
registry, download, artifact handling, filesystem install, `pip` integration,
authentication, signature enforcement, PKI, billing, or cloud API.

## GA recommendation

Ready for GA review after the RC-3 quality gates and local distribution audit
are complete. This document does not create a tag, publish a package, or start
GA work.
