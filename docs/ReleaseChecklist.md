# TKAI V7.0 Production Readiness Checklist

- [x] Confirm 7.0.0 across Python, Dashboard, AI Studio, API, and release metadata.
- [x] Verify all 15 V7 frameworks and the module/import dependency graph.
- [x] Verify V6 and TikTok backward compatibility.
- [x] Verify read-only OpenAPI projections and security boundaries.
- [x] Generate release, framework, integrity, checksum, source, and ZIP metadata.
- [x] Verify the canonical TikTok registry is unique, complete, and importable.
- [x] Verify package structure, import boundaries, and dependency graph integrity.
- [x] Run Ruff lint and normalize formatting.
- [x] Record full pytest, TikTok regression, deployment, release, production,
  and local-runtime results in `docs/ReleaseValidation.md`.
- [x] Record Dashboard and AI Studio production builds.
- [x] Generate and validate OpenAPI.
- [x] Validate operational PowerShell scripts.
- [x] Build source and release packages plus SHA-256 integrity manifests.
- [x] Confirm metrics, structured logging, audit, error reporting, and health endpoints.
- [x] Confirm secret filtering, RBAC, tenant/workspace isolation, safe defaults,
  plaintext-secret scanning, and absence of execution bypasses.
- [x] Repository-wide mypy duplicate-module failures are allowed only for known
  generated copies under `artifacts/`; record them as an existing issue.
- [x] Run Ruff, configured repository mypy, and full pytest.
- [x] Run TikTok, deployment, release, production, and local-runtime regression suites.
- [x] Build Dashboard and AI Studio production assets.
- [x] Validate PowerShell syntax and OpenAPI generation.
- [x] Validate startup, repeated shutdown, diagnostics, database initialization,
  backup, restore, and integrity through the production and local-runtime suites.
- [x] Validate release manifest, exclusions, checksums, and secret scan.
- [x] Run `git diff --check` and create the approved local annotated tag.

## Historical V3 checklist

- [x] Synchronize Python, Dashboard, Studio, and Helm metadata at `3.0.0`.
- [x] Review public compatibility and frozen Studio REST contract boundaries.
- [x] Run `pytest`, `ruff check .`, `black --check .`, `mypy src`, and
  `git diff --check`.
- [x] Validate offline wheel/sdist and fresh-install checks for the package and
  Studio backend.
- [x] Confirm MIT license metadata and default template package data.
- [x] Confirm Enterprise reference packages are included in wheel/sdist and
  importable from an isolated local wheel installation.
- [x] Document known limitations, rollback, operations, and future roadmap.
- [x] Confirm Enterprise remains reference-only with no authentication,
  persistence, enforcement, billing, cloud, or automatic layer integration.
- [x] Run Dashboard and Studio Node/Vite/typecheck/build validation.
- [ ] Validate Docker, Compose, Helm, and rendered Kubernetes resources.
- [x] Build and inspect the wheel and source distribution.
- [ ] Obtain release approval before creating tags, releases, or publishing.
