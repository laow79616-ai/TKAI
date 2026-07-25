# TKAI Platform Enterprise 1.0 Final Release Checklist

- [x] Confirm Runtime 1.3.0, SDK 2.0, Studio 2.1, Enterprise 3.0, and Platform
  Enterprise 1.0.0 mapping.
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
- [ ] Run Node/Vite/typecheck/ESLint in the intended frontend build environment.
- [ ] Obtain release approval before creating tags, releases, or publishing.
