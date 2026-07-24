# TKAI Studio V2.1 RC-3 Packaging and Release Validation

## Baseline

- RC-2 baseline: `dc16e89` (`chore(release): validate studio rc2 performance and reliability`)
- Branch: `feature/v2.1-studio-architecture`
- Package version: `1.3.0`
- Studio version: V2.1 reference product layer; it has no separate package version.

## Version and metadata audit

The canonical distribution version remains `1.3.0` in `pyproject.toml` and
`tkai.__version__`. The wheel metadata reports name `tkai`, version `1.3.0`,
MIT license with `License-File: LICENSE`, Python requirement `>=3.10`, and the
`tkai` console entry point. Studio release documents do not introduce a second
package version.

## Packaging validation

The local `build` module was unavailable, so no dependency was downloaded. The
RC used the offline fallback paths: `pip wheel --no-deps --no-build-isolation`
for the wheel and `setuptools.build_meta.build_sdist` for the sdist. Both
artifacts were generated successfully.

A release-blocking packaging defect was corrected in setuptools discovery:
the distribution had previously only scanned `src/`, excluding the top-level
`studio` Python package. Package discovery now includes `tkai*` and `studio*`,
while the Studio frontend source, static assets, and Studio docs are declared
as `studio` package data. The audited wheel and sdist contain Studio backend,
frontend layout, typed API client, route entry source, Studio docs, TKAI default
template data, README, and LICENSE. They exclude tests, benchmarks, caches,
`.git`, virtual environments, and credential-like local artifacts from the
wheel.

## Fresh install

A temporary virtual environment installed the local wheel with `--no-index`
and `--no-deps`. From outside the repository it successfully imported `tkai`
and `studio`, created `StudioDependencies`, read the default template resource
and Studio frontend API source via package resources, ran `tkai version show`,
`tkai --help`, and `tkai ai doctor --json`, and executed all offline SDK
examples. Temporary build directories and virtual environments are not release
artifacts and are removed after validation.

## Frontend packaging

The distribution includes the React/Vite project layout, static `index.html`,
typed API client, route declaration, and feature source. Node/npm dependencies
are not installed in this environment, so npm/Vite/TypeScript/ESLint execution
is not claimed. No frontend build output is bundled.

## Quality and recommendation

The RC-3 gate runs `pytest`, `ruff check .`, `black --check .`, `mypy src`, and
`git diff --check`, plus release tests three times. No network request, real
Provider, Studio server, database, or WebSocket is required.

Within the offline Python/package scope, there are no release blockers and the
recommendation is ready for Studio V2.1 GA preparation. Required target
environment follow-up: run frontend package installation, Vite build,
TypeScript typecheck, and ESLint with the intended Node toolchain.
