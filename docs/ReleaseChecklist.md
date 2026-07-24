# TKAI Platform 1.0 Release Checklist

- [x] Confirm Runtime 1.3.0, SDK 2.0, Studio 2.1, and Platform 1.0.0 mapping.
- [x] Review public compatibility and frozen Studio REST contract boundaries.
- [x] Run `pytest`, `ruff check .`, `black --check .`, `mypy src`, and
  `git diff --check`.
- [x] Validate offline wheel/sdist and fresh-install checks for the package and
  Studio backend.
- [x] Confirm MIT license metadata and default template package data.
- [x] Document known limitations, rollback, operations, and future roadmap.
- [ ] Run Node/Vite/typecheck/ESLint in the intended frontend build environment.
- [ ] Obtain release approval before creating tags, releases, or publishing.
