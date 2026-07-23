# Changelog

## Unreleased

### Added

- Optional explicit Redis distributed backend with lazy dependency loading,
  JSON-safe values, bounded reconnect attempts, lifecycle ownership, backend
  factory configuration, and offline injected-client coverage. `LocalBackend`
  remains the unchanged default implementation.
- Optional explicit distributed backend health probes with immutable cached
  snapshots, healthy/degraded/unhealthy status, synchronous/asynchronous
  checks, bounded retries, configurable periodic lifecycle, and offline Redis
  client coverage. Existing passive backend health behavior is unchanged.
- Optional explicit distributed failover manager with thresholded primary to
  local-memory fallback, recovery detection, manual failback, immutable metrics
  and snapshots, isolated EventBus events, and no automatic Runtime takeover.

## 1.2.0

### Added

- RC-2 release validation adds offline module benchmark manifests, bounded
  concurrency stress coverage, lifecycle/memory/snapshot/recovery validation,
  and a release checklist. These checks add no runtime integration or API.
- RC-3 packaging validation adds package-data coverage for the built-in default
  template manifest and README, plus offline wheel-install, import, CLI, and
  Doctor release smoke checks.

### General availability validation

- Final GA validation covers the optional Policy Engine, Retry Framework,
  EventBus/Telemetry, Local Distributed Backend, Adaptive Routing, and
  Multi-region foundations without changing V1 public APIs.
- Offline benchmark infrastructure, bounded stress validation, and lifecycle,
  snapshot, cleanup, failure-injection, and recovery validation are included in
  the release gate.
- EventBus subscriber isolation and concurrent Policy/Retry event-recording
  locking are covered by regression tests.
- Package-data validation includes the default template manifest and README;
  fresh wheel installation, CLI, Doctor, and import smoke checks are offline.
- The distribution is licensed under the MIT License.

- Optional multi-region routing foundation with immutable region metadata,
  explicit topology and adapters, local diagnostics, CLI support, and EventBus
  events. It retains single-region defaults and performs no network failover.
- Optional adaptive routing foundation with bounded local signal history,
  deterministic scoring, explicit Runtime and Policy adapters, Doctor support,
  CLI diagnostics, and EventBus events. It does not enable multi-region routing
  or replace existing routing defaults.

### Added

- Optional V1.2 Policy Engine foundation with explicit pipeline stages,
  stable priority ordering, failure isolation, compatibility adapters,
  EventBus events, Doctor diagnostics, and `tkai ai policy` inspection.
- Optional V1.2 Retry Framework foundation with explicit local budgets,
  deterministic backoff, exception classification, Policy Engine adapter,
  EventBus events, Doctor diagnostics, and `tkai ai retry` inspection.
- Optional V1.2 Distributed Runtime foundation with LocalBackend, membership,
  cooperative heartbeat, local locks, explicit Runtime/Policy adapters,
  EventBus events, Doctor diagnostics, and `tkai ai distributed` inspection.
- Optional V1.2 Telemetry foundation with LocalExporter, metrics, traces,
  correlation context, safe structured logs, explicit adapters, Doctor, and CLI.

- V1.1 RC-1 public-API inventory, compatibility/import regression coverage,
  serialization safety checks, CLI/Doctor smoke validation, and release
  checklist documentation.
- V1.1 RC-2 offline benchmark runner, routing/cache/rate-limit/EventBus/plugin
  benchmark scripts, concurrent stress tests, 100,000-iteration soak checks,
  and performance/reliability release documentation.
- V1.1 RC-3 local wheel/sdist artifact validation, isolated-environment install
  checks, offline cache/plugin/custom-routing examples, and release notes.
- Optional V1.1 local foundations for credential discovery, persistent
  configuration, passive health, observability, circuit breaking, cost/load
  routing, rate limiting, cache, and the Plugin SDK.

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
- V1.1 additive foundations remain opt-in and preserve the V1 provider,
  configuration, CLI, and legacy plugin lifecycle behaviour.
- EventBus and RateLimitManager now protect their local concurrent state
  transitions during publish and quota consumption.

### Known limitations

- Local-memory implementations only; no Redis backend or real distributed
  synchronization.
- No automatic failover, active health probing, traffic migration, ML routing,
  or OpenTelemetry SDK integration.
- The V1.2 foundations are opt-in and do not automatically take over existing
  ProviderManager, Runtime, or AIClient behavior.

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
