# TKAI

TKAI is a typed, offline-testable Python framework for project scaffolding,
plugins, workflows, and provider-neutral AI integrations.

Current release: **1.3.0**.
Previous general availability release: **1.2.0**.

## TKAI Platform 1.0

Platform 1.0 documents the compatible Runtime 1.3.0, SDK 2.0, and Studio 2.1
layers. It does not introduce a second Python package version; the published
`tkai` distribution remains **1.3.0**. See the [platform overview](docs/Platform.md),
[installation guide](docs/Installation.md), [release notes](docs/ReleaseNotes.md),
and [release checklist](docs/ReleaseChecklist.md).

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
