# TKAI

Current release candidate: **10.0.0**. TKAI V10 adds eleven read-only sovereign
platform components while preserving V6, V7, V8, V9, TikTok, local-runtime,
dashboard, AI Studio, deployment, configuration, storage, security, and
extension behavior. See [the V10 overview](docs/v10/COMPONENT_OVERVIEW.md) and
[release notes](RELEASE_NOTES_V10.md).

TKAI is a typed, offline-testable Python framework for project scaffolding,
plugins, workflows, and provider-neutral AI integrations.

Previous general availability releases: **9.0.0**, **8.0.0**, **7.0.0**, and
**6.0.0**.
Historical release documentation, including **1.2.0**, remains available in
`docs/release`.

## TKAI V10.0 Production Readiness

TKAI V10 consists of exactly eleven sovereign, authenticated, read-only
components. It adds no business functionality, execution capability, runtime
mutation, automatic migration, or automatic approval. Existing V6 through V9
APIs and operational behavior remain compatible. Operators should review the
[architecture](docs/v10/ARCHITECTURE_OVERVIEW.md),
[security guide](docs/v10/SECURITY_GUIDE.md),
[operations guide](docs/v10/PRODUCTION_OPERATIONS_GUIDE.md), and
[V9 upgrade guide](docs/v10/UPGRADE_V9_TO_V10.md).

## TKAI V9.0 General Availability Release

TKAI V9.0 finalizes exactly ten adaptive, authenticated, read-only components.
It introduces no new business features and changes neither TikTok nor existing
framework behavior. V6, V7, and V8 APIs, configuration, storage, extensions,
Dashboard, AI Studio, OpenAPI, deployment, and local-runtime contracts remain
backward compatible. See the [V9 component overview](docs/v9/README.md),
[deployment guide](docs/v9/Deployment-Guide.md),
[operations guide](docs/v9/Production-Operations-Guide.md),
[Windows guide](docs/v9/Windows-Local-Guide.md),
[upgrade guide](docs/v9/Upgrade-V8-to-V9.md),
[known issues](docs/v9/Known-Issues.md),
[security notes](docs/v9/Security-Guide.md), and
[compatibility notes](docs/v9/Compatibility-Guide.md).

## TKAI V8.0 General Availability Release

TKAI V8.0 finalizes the Hyper Kernel and ten additive Hyper frameworks as an
official GA release. It introduces no new business features, does not modify
TikTok behavior, and does not change existing framework behavior. V6 and V7
APIs, configuration, storage, extensions, Dashboard, AI Studio, OpenAPI, and
deployment contracts remain backward compatible.

The final V8 inventory contains exactly 11 completed frameworks. See the
[V8 release notes](RELEASE_NOTES_V8.md), [architecture overview](docs/v8/Architecture.md),
[framework overview](docs/v8/FrameworkOverview.md),
[deployment guide](docs/v8/Deployment-Guide.md),
[operations guide](docs/v8/Operations-Guide.md),
[Windows guide](docs/v8/Windows-Guide.md),
[upgrade guide](docs/v8/Upgrade-V7-to-V8.md),
[known issues](docs/v8/Known-Issues.md),
[security notes](docs/v8/Security-Guide.md), and
[compatibility notes](docs/v8/Compatibility.md).

## TKAI V7.0 Production Release

TKAI V3.0 established the unified runtime and distribution baseline. TKAI V7.0
adds opt-in, metadata-oriented platform frameworks while preserving the V6
runtime, SDK, Agent Runtime, Plugin Marketplace,
Enterprise Platform, Cloud Native deployment, AI Studio, and Enterprise
Marketplace into one versioned distribution. Existing 1.x runtime and 2.x SDK
interfaces remain supported unless explicitly listed in the upgrade guide. See the
[platform overview](docs/Platform.md),
[installation guide](docs/Installation.md), [release notes](docs/ReleaseNotes.md),
[release checklist](docs/ReleaseChecklist.md), [V3.0 release guide](docs/release/V3.0.md),
the [V5 module catalog](docs/V5Modules.md), [local quick start](docs/QuickStart.md),
and [V7.0 production-readiness notes](RELEASE_NOTES_V7.md).

V7.0 is a release-quality consolidation of the existing TikTok platform. It
does not add social platforms, broaden execution privileges, or change the
existing functional scope. Production operators should review the
[deployment guide](docs/Deployment.md), [Windows guide](docs/LocalWindows.md),
[troubleshooting guide](docs/Troubleshooting.md), [upgrade guide](docs/Upgrade.md),
and [release checklist](docs/ReleaseChecklist.md). Final release metadata is
recorded in [RELEASE_MANIFEST.json](RELEASE_MANIFEST.json),
[BUILD_METADATA.json](BUILD_METADATA.json), and
[VERSION_SUMMARY.md](VERSION_SUMMARY.md).

The V7 framework catalog and release evidence are in
[Framework Overview](docs/v7/FrameworkOverview.md) and
[Production Readiness Report](docs/v7/ProductionReadinessReport.md). Review
[V6 compatibility](docs/v7/Compatibility.md), [security notes](docs/v7/SecurityNotes.md),
and [known issues](docs/KnownIssues.md) before deployment.

## AI provider framework

The public AI layer keeps legacy `AIClient.generate()` available while adding
normalized chat, streaming, embeddings, async calls, capability routing,
fallback policy, diagnostics, and a thin `tkai ai` CLI. Provider transports
are injectable, so tests and examples never require credentials or network
access.

```bash
python -m pip install -e '.[dev]'
tkai ai doctor
tkai ai providers --json
tkai ai capabilities --json
tkai ai fallback --json
```

See [AI framework](docs/AI.md), [provider development](docs/Providers.md),
[CLI guide](docs/CLI.md), [Doctor guide](docs/Doctor.md), and the
[release checklist](docs/Release.md).

## Compatibility

`AIClient`, `AIProvider`, `ProviderManager`, `OpenAICompatibleProvider`, and
existing synchronous CLI commands remain supported. Async provider methods and
the `tkai ai` inspection commands are additive. Details are in the
[migration guide](docs/Migration.md).

## Development validation

```bash
python -m pytest
python -m ruff check .
python -m black --check .
python -m mypy src
```

All executable AI examples are under `examples/ai/` and intentionally use
local fakes only.

## TKAI 2.0 SDK reference layers

The additive SDK reference layers provide explicit Agent adapters, local
Provider, Memory, Workflow, Tool, and Plugin contracts for offline development.
They do not modify V1.x Runtime behavior or enable external services. See the
[SDK guide](docs/SDK.md) and the [TKAI 2.0 RC-3 release validation](docs/release/tkai-2.0-rc3.md).

## TKAI Enterprise V3.0 reference foundations

The distributable package also includes additive, offline Enterprise reference
contracts for identity, organization, tenant, authorization, audit, and
licensing. They do not enable authentication, persistence, authorization
enforcement, or cloud services. See the [Enterprise guide](docs/Enterprise.md)
and [Enterprise RC-3 validation](docs/release/enterprise-v3-rc3.md).

## License

TKAI is released under the [MIT License](LICENSE).

## TKAI V8

Version 8.0.0 provides 11 additive Hyper components with read-only advisory APIs. See [V8 release notes](RELEASE_NOTES_V8.md) and [production operations](docs/v8/Production-Operations-Guide.md).
