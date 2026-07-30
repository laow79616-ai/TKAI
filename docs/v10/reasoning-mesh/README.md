# V10 Sovereign Reasoning Mesh

The Sovereign Reasoning Mesh is TKAI's local-first, deterministic, bounded, read-only
reasoning-reference layer across completed V6–V10 components. It stores immutable
profiles, contexts, claim and premise summaries, evidence and inference references,
assumptions, constraints, alternatives, confidence, uncertainty, contradictions,
safe explanations, and advisory assessments.

## Architecture and integrations

Caller-supplied metadata enters bounded, scope-isolated in-memory registries. Evidence
is referenced (never ingested) from the V10 knowledge, integrity, trust, governance,
and compatibility meshes, V9 adaptive meshes, and existing V6–V8 providers.
Compatibility records cover V6, V7, V8, V9, and V10 without migration, upgrade, or
rollback. Governance, integrity, trust, and knowledge integrations are references only.
Internal event names use the V7 Event Fabric metadata compatibility interface; no
external broker is used.

## Security and safety

Only safe user-facing summaries are accepted. Hidden chain-of-thought, private
scratchpads, token traces, hidden prompts, model secrets, credentials, and secret
context are rejected or redacted. The mesh performs no filesystem scan, external
search, network call, reasoning execution, automatic selection, decision, planning,
approval, policy execution, mutation, service control, deployment, recovery, browser,
account, device, proxy, publishing, outreach, or TikTok action.

## Operations and Windows local guide

Use the GET-only `/v10/reasoning/*` endpoints for bounded projections, diagnostics,
health, metrics, audit, and lifecycle metadata. Apply tenant/workspace/namespace RBAC
at the caller boundary. On Windows, run from the repository root with the local virtual
environment and use `python -m pytest tests/v10/reasoning_mesh`. No cloud service,
browser, real account, cookie, session, proxy, or external network is required.
