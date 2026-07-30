# V8 Hyper Simulation & Forecasting Fabric

The fabric is an advisory, offline, metadata-driven V8 framework. It reads bounded,
allowlisted V6, V7, and V8 references, validates immutable contracts, runs only local
deterministic calculations, and exposes read-only projections. It has no TikTok,
browser, account, scheduler, allocator, runtime-mutation, external-network, or
automatic-approval capability.

## Model and data flow

Profiles reference inputs, baselines, local model metadata, scenarios, assumptions,
constraints, governance, and compatibility. Inputs contain value references rather
than sensitive values. Simulations produce result references. Forecasts always carry
uncertainty references and limitations. Evaluations require factors, weights,
supporting references, limitations, and an explanation.

Models are limited to `bounded-deterministic`, `rule-table`, and `linear-trend`.
Correlation is never represented as causation. Assumptions serialize with
`is_fact=false`; recommendations serialize with `executable=false`.

## Bounds, security, and safety

Default bounds are 3,660 horizon units, 1,000 inputs, 100 scenarios, 100 simulations,
100 forecasts, 100 source records per adapter call, and 1 MB result metadata. RBAC
enforces tenant, workspace, namespace, and profile isolation. Secret-like keys are
redacted from safe metadata, logs, source projections, and diagnostics.

`approved-reference` confirms only an artifact. It never authorizes execution.
Pause, kill-switch, governance, risk, and security conditions remain advisory
constraints and cannot be bypassed.

## Forecasting and evaluation

Supported metadata covers trend, capacity, resources, schedules, dependencies, risk,
recovery, governance, health, workload, queue, storage, confidence calibration,
comparisons, reviews, version history, analytics, health, metrics, events, and audit.
Forecast quality is evidence-relative; unsupported certainty claims are prohibited.

## Compatibility and operations

Adapters are read-only and reference existing V6 AI centers, V7 frameworks/Event
Fabric, and V8 frameworks without duplicating their infrastructure. No existing API
or business behavior is changed.

All `/v8/simulation/*` routes are GET-only. Run locally on Windows with:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v8\hyper_simulation
.\.venv\Scripts\python.exe -m ruff check src\tkai\v8\hyper_simulation
.\.venv\Scripts\python.exe -m mypy src\tkai\v8\hyper_simulation
```

Operational review should verify audit records, adapter health, input freshness,
uncertainty and limitations, dependency diagnostics, governance references, pause
state, kill-switch state, and compatibility before treating an artifact as an
approved reference.
