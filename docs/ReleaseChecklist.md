# TKAI V5.0 Local Production Release Checklist

- [ ] Confirm 5.0.0 across Python, Dashboard, AI Studio, API, and release metadata.
- [ ] Run Ruff, focused mypy, repository mypy, and full pytest.
- [ ] Run TikTok, deployment, release, and local-runtime regression suites.
- [ ] Build Dashboard and AI Studio production assets.
- [ ] Validate PowerShell, OpenAPI, startup, repeated shutdown, and diagnostics.
- [ ] Validate database initialization, backup, restore, and integrity.
- [ ] Validate release manifest, exclusions, checksums, and secret scan.
- [ ] Run `git diff --check`; obtain approval before tagging, publishing, or pushing.

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
