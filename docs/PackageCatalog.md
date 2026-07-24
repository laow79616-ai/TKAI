# TKAI Marketplace V5 Package Catalog Foundation

## Scope

Package Catalog Foundation provides immutable local package manifests, search
models, and a reference in-memory catalog. It is additive to Marketplace V5
and does not modify the original Marketplace Registry, Runtime, SDK, Studio,
Enterprise, or Cloud.

No network, download, installation, package signature, Registry implementation,
dependency resolver, artifact, or persistence is implemented.

## Package model

The `marketplace.package_catalog` namespace provides its own catalog-oriented
`PackageDescriptor` around `PackageManifest`. This deliberately preserves the
Sprint-1 `marketplace.PackageDescriptor` import path unchanged.

`PackageManifest` records explicit package id, publisher id, name, description,
`PackageVersion`, category, tags, compatibility, dependency descriptors, and
metadata. All models are frozen and JSON-safe.

Supported `PackageCategory` values are Provider, Workflow, Tool, Plugin, Memory,
Template, and Extension. `PackageMetadata` and `PackageIconDescriptor` are
descriptive only and never load an icon or package artifact.

## Compatibility and dependency declarations

`PackageCompatibility` (also exported as `CompatibilityDescriptor`) describes
Runtime, SDK, Studio, Enterprise, and Cloud version expectations. It does not
evaluate compatibility or select a platform version.

Existing `PackageDependency` descriptors may be embedded in a manifest. The
catalog stores them as declarations only; it does not resolve, download, lock,
or install dependencies.

## Catalog and search

`MarketplaceCatalog` supports stable `list`, `get`, `filter`, `sort`, `search`,
and `snapshot` operations over a caller-provided local source. `PackageQuery`,
`PackageFilter`, `PackageSort`, and `PackageSearchResult` model category,
publisher, tag, version, and keyword searches entirely in memory.

`ReferenceCatalogService` is a thread-safe, in-memory test/reference service.
Its `register` and `unregister` methods only manipulate its own descriptor map;
they do not use, modify, or replace the Marketplace Registry.

## Current limitations

- No remote catalog, Registry, publisher lookup, or network transport.
- No package download, upload, artifact extraction, installation, or update.
- No signature check, trust evaluation, dependency resolver, or lock file.
- No compatibility enforcement, Runtime hook, SDK hook, Studio middleware,
  Enterprise integration, or Cloud integration.
