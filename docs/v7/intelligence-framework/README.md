# V7 Unified Intelligence & Decision Framework

## Architecture and intelligence model

This local-only framework stores immutable metadata for profiles, contexts, source
references, evidence, knowledge references, signals, observations, reasoning
summaries, hypotheses, explainable evaluations, decisions, alternatives,
comparisons, confidence, recommendations, explanations, reviews, approvals,
governance, versions, history, analytics, health, metrics, and audit.

It is advisory and read-only at its integration boundaries. It has no executor,
autonomous decision API, write API, external network client, runtime mutation,
automatic approval, browser action, account action, publishing action, or
workflow/scheduler/resource mutation.

## Evidence, reasoning, decisions, and explainability

Sensitive evidence is reference-only and integrity-hashed. Observations are not
facts or causal conclusions. Hypotheses are labelled and require falsification
criteria. Reasoning records contain only safe summaries and references; chain of
thought and hidden reasoning are prohibited. Every evaluation score requires
factors, supporting references, limitations, weights, and an explanation.
Decisions, recommendations, and approvals never authorize execution.

## Integrations and compatibility

The source registry declares bounded, read-only adapters for all completed V7
frameworks and the existing V6 intelligence, learning, knowledge, decision,
prediction, planning, governance, strategy, risk, BI, performance, and analytics
centers. Adapters reference existing infrastructure and never duplicate it.
Existing V6, TikTok, dashboard, OpenAPI, deployment, and V7 behavior is unchanged.

## Security, safety, and governance

Every artifact carries tenant, workspace, and namespace scope. Cross-scope
references fail closed. Metadata rejects secret-like fields and nested/unbounded
values. Evidence/source/result counts and time ranges are bounded. Diagnostics
never include secrets. Governance metadata records policy, review, approval,
risk, pause, kill-switch, and audit requirements without executing policies.

## API and dashboard

All `/v7/intelligence/*` routes are GET-only projections. Query parameters require
tenant and workspace and accept an optional namespace. The dashboard projection
uses the same isolated read model. No secret-value, hidden-reasoning, execution,
automatic-approval, or mutation route exists.

## Operations and Windows local guide

From PowerShell at the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v7\intelligence_framework
.\.venv\Scripts\python.exe -m ruff check src\tkai\v7\intelligence_framework
.\.venv\Scripts\python.exe -m mypy src\tkai\v7\intelligence_framework
```

The framework needs no network, TikTok account, cookie, session, proxy, browser,
cloud service, AI provider, or external decision service.
