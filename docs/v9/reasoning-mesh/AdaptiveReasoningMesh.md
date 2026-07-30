# TKAI V9 Adaptive Reasoning Mesh

## Architecture

The Adaptive Reasoning Mesh is a local, metadata-only federation and advisory
reasoning layer across V6, V7, V8, and V9. Immutable contracts feed
isolation-aware registries, deterministic evaluation and confidence projections,
safe explanations, governance references, diagnostics, metrics, dashboard
projections, and GET-only API adapters. It never owns or duplicates upstream
knowledge or evidence payloads.

## Federation, contexts, sources, and knowledge references

Federation accepts only allowlisted local framework references and enforces a
bounded source count. It performs no remote discovery and no network access.
Contexts carry tenant, workspace, namespace, profile, and context coordinates.
Knowledge and sensitive evidence remain references with provenance, lineage,
version, integrity, freshness, and confidence metadata.

## Evidence, signals, observations, hypotheses, and assumptions

Evidence metadata is immutable and payload-reference-only. Observations are
explicitly distinct from facts and causal conclusions. Hypotheses and assumptions
are always labeled and expose validation status, contrary evidence, falsification
criteria, risks, and limitations.

## Constraints, reasoning metadata, alternatives, and comparisons

Sessions retain safe summaries, links, evaluations, confidence, explanations, and
limitations only. Chain-of-thought, hidden reasoning, private deliberation,
scratchpads, and raw reasoning traces are rejected. Constraints bound sources,
evidence, knowledge, hypotheses, alternatives, time ranges, and result sizes.
Comparisons reject unsupported causal conclusions.

## Evaluations and confidence calibration

Evaluation types are fixed and use transparent, bounded weighted factors. Every
result includes factors, weights, references, limitations, and an explanation.
Confidence calibration uses named evidence, knowledge, source, freshness, risk,
compatibility, and governance factors and never claims certainty.

## Recommendations, explainability, and reviews

Recommendations are advisory, reference-only, and non-executable. Explanations
project evidence used and missing, sources, observations, hypotheses, assumptions,
constraints, policies, risks, confidence, evaluation breakdown, limitations, and
review requirements without revealing hidden reasoning. Review records are
immutable metadata.

## Governance, versioning, compatibility, history, and analytics

Governance integration is reference-only and pause-, maintenance-, and
kill-switch-aware. Approved Reference approves only an advisory artifact and never
execution. Versioning is immutable; V6-V9 compatibility performs no automatic
migration. History, analytics, diagnostics, health, metrics, and audit are
read-only projections.

## Security and safety

RBAC-compatible authorization enforces tenant, workspace, namespace, profile, and
context isolation. Secret filtering and safe-metadata validation prevent secrets
and hidden reasoning from logs, diagnostics, explanations, or retrieval. The mesh
cannot execute TikTok, browser, account, device, proxy, publishing, outreach,
workflow, scheduling, recovery, configuration, or runtime actions.

## Operations and Windows local guide

The API routes under `/v9/reasoning/` are GET-only. There are no write, execution,
approval, external-AI, hidden-reasoning, scratchpad, or secret retrieval routes.

```powershell
.\.venv\Scripts\python.exe -m ruff check src\tkai\v9\reasoning_mesh
.\.venv\Scripts\python.exe -m mypy src\tkai\v9\reasoning_mesh
.\.venv\Scripts\python.exe -m pytest tests\v9\reasoning_mesh -q
```

The tests are offline and require no TikTok access, accounts, cookies, sessions,
proxies, browser, external network, external AI, cloud service, or runtime mutation.
