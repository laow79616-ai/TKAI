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
# TKAI V6.0 Production Readiness Validation

Validated on 2026-07-29 from
`feature/tiktok-v6-production-readiness`.

| Gate | Result |
| --- | --- |
| Repository path and branch | PASS |
| Ruff lint | PASS |
| Ruff formatting | PASS; 133 existing files normalized |
| Full pytest | PASS; 1,256 passed, 1 skipped |
| TikTok/deployment/release/local/production suites | PASS; 344 passed |
| Dashboard production build | PASS |
| AI Studio production build | PASS |
| OpenAPI generation | PASS; 650 unique paths |
| Operational PowerShell syntax | PASS |
| Source distribution | PASS; `tkai-6.0.0.tar.gz` |
| Windows release package | PASS; manifests and SHA-256 verified |
| Dependency integrity | PASS; `pip check` |
| Module registry/import graph | PASS; 38 unique importable modules |
| Tracked-source secret scan | PASS |
| Full mypy | KNOWN ISSUE; stops on duplicate generated modules under `artifacts/` |
| GA host prerequisites | WARNING; optional twine, SQLAlchemy, Alembic, and psycopg are not installed on the validation host |

The full and targeted suites cover metrics registration, structured logging,
audit records, error reporting, health endpoints, RBAC, tenant/workspace
isolation, secret filtering, safe defaults, and execution boundaries. No
source-package duplicate modules, plaintext secrets, or execution bypasses
were detected.

The only known repository-wide issue is duplicate packaged modules in existing
generated artifact directories. Generated artifacts are excluded from source
control and must not be added to Python or mypy import roots.

No code release blocker remains. Deployment operators must install and verify
the optional production database and publication dependencies before an
external deployment or package publication.
