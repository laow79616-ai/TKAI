# Changelog

## Unreleased

### Added

- Workflow runtime checkpoints, recovery, cooperative pause/resume/cancel,
  and native asyncio control boundaries.
- `tkai workflow checkpoint`, `resume`, and `doctor` commands, plus JSON/YAML
  run input and machine-readable result output.
- `checkpoint-example` and `pause-resume-example` built-in workflows.
- Provider-neutral chat, embedding, configuration, manager, and error APIs.
- Offline-testable OpenAI-compatible and OpenRouter provider adapters.
- Async provider runtime, SyncBridge compatibility layer, injectable async HTTP
  transport, SSE/stream normalization, and transport adapter compatibility.
- Provider registry aliases, async/sync/stream manager routing, typed
  capability declarations, exact model capability overrides, and explanatory
  no-match errors.
- Independent provider fallback policy with ordered candidates, retry budgets,
  blacklists, safe failure summaries, and pre-first-chunk stream failover.
- Read-only AI Doctor reports with safe JSON/text output and `tkai ai` service
  inspection commands for providers, capabilities, fallback, validation,
  version, and framework information.
- Offline executable AI examples, migration guidance, provider development,
  Doctor, CLI, and V1.0 release-checklist documentation.

### Changed

- Workflow release documentation now describes runtime architecture, state
  transitions, compatibility, and operational limitations.
- V1.0 RC release validation now covers public AI compatibility, offline
  examples, documentation, quality gates, and tag-ready metadata.

## 1.0.0-rc.1

### Added

- Plugin discovery, loading, registry, and lifecycle APIs.
- Bundled discoverable plugin manifests for Python, Docker, Git, OpenAI,
  Claude, Gemini, Telegram, and TikTok.
- Workflow tasks, steps, event bus, executor, and serial/parallel scheduler.
- Unified AI provider interfaces and identities for OpenAI, Claude, Gemini,
  DeepSeek, Qwen, and OpenRouter.

### Changed

- Unified configuration state handling through `Settings` and the compatible
  `ConfigManager` persistence facade.
- Unified the two historical `TemplateManager` import paths behind one API.
- Added packaging and quality-tool configuration to `pyproject.toml`.

### Fixed

- Prevented `tkai.__main__` from executing the CLI when imported.
- Prevented template discovery from treating `__pycache__` as a template.

## 0.2.1

- Initial packaged TKAI command-line and template-generation release.
