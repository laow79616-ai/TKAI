# TKAI 8.0.0 Release Notes

TKAI V8 completes the Hyper Kernel and ten Hyper frameworks. This production-readiness
change adds no business or execution capabilities. V6, V7, TikTok, dashboard, AI
Studio, local-runtime, deployment, configuration, storage, extension, security, and
OpenAPI behavior remain compatible.

## Frameworks

Exactly 11 completed V8 components are recorded in `FRAMEWORK_MANIFEST_V8.json`.
All V8 HTTP surfaces are read-only advisory, diagnostics, health, or metadata routes.

## Upgrade

V8 is additive. Existing V6 and V7 callers require no route or configuration changes.
Review `docs/v8/Upgrade-V7-to-V8.md` before enabling V8 integrations.
