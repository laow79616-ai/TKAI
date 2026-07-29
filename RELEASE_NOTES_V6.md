# TKAI V6.0 Release Notes

TKAI V6.0 prepares the existing TikTok Cloud Control Platform for production.
It adds no business features, social platforms, or execution capabilities.

## Release-quality work

- Version metadata is synchronized at 6.0.0 across Python, API, Dashboard,
  AI Studio, Helm, and release manifests.
- The TikTok module registry is validated for uniqueness, importability, and
  one-time route registration.
- Ruff lint and formatting, full and targeted pytest suites, frontend builds,
  OpenAPI generation, PowerShell parsing, package validation, secret scanning,
  and diff checks form the release gate.
- Health, metrics, logging, audit, error reporting, RBAC, tenant/workspace
  isolation, secret filtering, and safe defaults are explicitly reviewed.
- Source and Windows release archives include build metadata and SHA-256
  integrity manifests.

## Compatibility and known issues

V5 public APIs and execution boundaries remain intact. Repository-wide mypy
may stop on duplicate packaged modules under generated `artifacts/`; this is an
existing artifact-layout issue, not a duplicate in the source package. Any
duplicate module outside `artifacts/` remains a release blocker.

See `docs/ReleaseValidation.md` and `docs/ReleaseChecklist.md` for the recorded
gate results and any remaining blockers.
