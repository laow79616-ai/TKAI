# Marketplace Server V2 Release Validation

## Release Summary

Marketplace Server V2 combines the existing reference foundations with an
optional FastAPI API, read-only resource APIs, single-administrator
authentication, a React dashboard source project, PostgreSQL persistence,
local Docker Compose configuration, production-hardening primitives, and the
Enterprise reference feature set. The foundations and public API contracts are
not changed by this release-validation work.

## Validation Scope

- Package metadata, manifest declarations, migrations, documentation, and
  dashboard source assets are audited as distributable package data.
- A wheel is built offline with setuptools and inspected for Server modules,
  migrations, dashboard assets, and metadata.
- The wheel and its declared `server` extra metadata are inspected. The base
  `tkai` package intentionally does not install optional HTTP Server
  dependencies. A full clean `server`-extra install remains pending in an
  environment that provides the declared dependencies.
- Release tests provide offline checks for Compose topology, migration
  configuration, HTTP application composition, authentication contracts,
  Enterprise API contracts, and compatibility imports.

## Deployment

`docker-compose.yml` defines an intentionally local development topology:
PostgreSQL, API, and Dashboard. The API is configured to run bounded migration
startup before serving requests. See `docs/deployment/DockerCompose.md` for
operator instructions and environment variables.

Install the Server capability with the declared optional dependencies:

```text
pip install "tkai[server]"
```

This validation environment does not provide Docker, Node/npm, or
`python -m build`; it also lacks an installable FastAPI distribution for an
offline `server`-extra installation. Therefore an actual Compose startup,
Dashboard browser smoke test, full Server application-factory install smoke,
and standard sdist build/install cannot be performed here. Those steps remain
required before an external GA decision.

## Compatibility

The reference Runtime, SDK, Studio, Marketplace Foundation, and Marketplace
Server module imports remain independent of this release work. Enterprise
continues to use `ReferenceEnterpriseStorage`; there is no Enterprise
PostgreSQL adapter in V2.

## Known Limitations

- Docker Compose is a local-development deployment only; it has no production
  TLS, secret manager, backups, scaling, or high-availability support.
- The dashboard source is packaged, but no frontend production bundle is
  generated during Python packaging.
- A base-only `tkai` installation does not include optional Server API
  dependencies; use the `server` extra for Marketplace Server imports.
- The clean `server`-extra installation has not been executed because the
  local environment cannot resolve FastAPI without network or a local package
  artifact.
- PostgreSQL integration remains opt-in and its live integration test is
  skipped when no PostgreSQL DSN is provided.
- Enterprise storage is reference-memory only.

## GA Recommendation

**Not ready for an external GA declaration from this environment.** The
Python quality gates and offline wheel validation can pass, but a clean sdist
install and a real Docker Compose/API/Dashboard smoke test must be completed
in an environment with the required build and container tooling.
