# TKAI

TKAI is a typed, offline-testable Python framework for project scaffolding,
plugins, workflows, and provider-neutral AI integrations.

Current release: **7.0.0**.
Previous general availability release: **1.3.0**.
Earlier supported release documentation remains available for **1.2.0**.

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
[Production Readiness Report](docs/v7/ProductionReadinessReport.md).

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
