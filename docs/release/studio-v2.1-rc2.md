# TKAI Studio V2.1 RC-2 Performance and Reliability Validation

## Baseline and scope

- RC-1 baseline: `61fe639` (`chore(release): establish studio v2.1 rc1 integration baseline`)
- Branch: `feature/v2.1-studio-architecture`
- Scope: offline benchmark, stress, reliability, lifecycle, cleanup, and
  regression validation only.

No Studio feature, frozen REST endpoint, OpenAPI schema, response envelope,
SDK public API, V1.x Runtime behavior, Workflow Designer, Execution Monitor,
or Agent Chat contract is changed by RC-2.

## Benchmark validation

`benchmarks.studio` provides bounded, fixed-seed scenarios for Studio backend,
frozen REST controllers, Workflow Designer reference payloads, Execution
Monitor reference snapshots, Agent Chat reference conversations, SDK Gateway,
repository, and service reads. Each scenario returns the existing
`BenchmarkResult` and renders deterministic Markdown and JSON via
`BenchmarkReport`. Results are structural only; RC-2 sets no machine-dependent
operations-per-second or latency threshold.

The Designer, Monitor, and Chat measurements cover only serializable frontend
reference payload handling because frontend dependencies are not installed in
this environment. They do not claim browser, Vite, React rendering, or
TypeScript execution performance.

## Stress and reliability validation

Bounded concurrency checks cover local Studio repositories and read-only
controller reports, confirming no duplicate IDs, deadlock, or residual worker
thread. Static frontend-store checks confirm there is no direct `fetch`, default
timer, or background polling side effect.

Reliability checks cover unconfigured Gateway execution failure with exception
chaining, a fresh successful host after failure, API validation failure,
malformed frontend snapshot/error paths, and idempotent lifespan/dependency
shutdown. No real Provider, API key, network service, server process,
filesystem persistence, or database is used.

## Quality results

The release gate runs `pytest`, `ruff check .`, `black --check .`, `mypy src`,
and `git diff --check`. Benchmark, stress, and reliability suites are each run
three times. All checks are deterministic and offline.

## Known limitations

- No browser/Vite/TypeScript/ESLint validation without a Node-enabled frontend
  environment and installed frontend dependencies.
- No real HTTP FastAPI server, WebSocket, authentication, database, live
  execution polling, real Provider, Agent Chat transport, or streaming chat.
- The frontend product layers remain reference contracts and fixtures.

## RC-3 recommendation

Ready for RC-3 packaging and release validation within the offline Python scope.
Frontend build tooling remains a required target-environment validation item.
