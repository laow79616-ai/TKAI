# TKAI Marketplace V5 Architecture

## Scope

TKAI Marketplace is an additive, reference-only product layer above the TKAI
Platform. It does not modify Runtime, SDK, Studio, Enterprise, Cloud, their
public APIs, or default behavior. Any future interaction with Platform must use
an explicit `PlatformGateway` adapter supplied by the host.

No network, package download, artifact storage, package installation, signature
verification, cloud service, or automatic integration is implemented here.

## Architecture

```text
Marketplace API / Catalog (future explicit adapters)
                    |
                    v
Registry -> Package Descriptor -> Dependency Graph
                    |
                    +-> Publisher / Version / Signature boundary
                    |
                    +-> Platform Gateway (explicit, future)
```

`MarketplaceRegistry` stores immutable package declarations in memory.
`MarketplaceCatalog` is a read-only local view. `ReferenceMarketplace` composes
them for examples and tests only; publishing means local descriptor registration,
not uploading a package.

## Packages

`PackageDescriptor` supports these declarative kinds:

- Plugin
- Provider
- Memory
- Workflow
- Tool

Each descriptor has an explicit id, name, `PackageVersion`, publisher,
capabilities, optional dependency declarations, signature text, and defensive
metadata. It contains no executable artifact, credential, token, or payload.

## Version and dependency contracts

`PackageVersion` is a small immutable semantic-version descriptor. A
`PackageDependency` declares an id and optional version constraint.
`DependencyGraph` produces a deterministic dependencies-first order and detects
missing or cyclic required dependencies. It does not resolve remote versions,
download artifacts, or install anything.

The [Package Catalog Foundation](PackageCatalog.md) adds a separate,
catalog-oriented manifest and local search namespace while preserving the
original Marketplace architecture imports unchanged.

## API and extension boundaries

`MarketplaceAPI`, `PackageInstaller`, `SignatureVerifier`, and
`PlatformGateway` are Protocols only. They reserve future integration points for
catalog transport, installation, signature validation, and Platform capability
queries without binding this release to a particular registry or cloud service.

## Current limitations

- No remote registry, search, publisher account, or network transport.
- No package download, extraction, installation, update, or uninstall.
- No package signature implementation, key management, or trust policy.
- No dependency version solver, lock file, or artifact cache.
- No Cloud implementation or automatic Runtime, SDK, Studio, Enterprise, or
  Cloud integration.
