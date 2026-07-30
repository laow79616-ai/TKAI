# TKAI V9 Adaptive Meta-Kernel

## Architecture

The V9 Adaptive Meta-Kernel is a local, metadata-driven coordination and
assessment layer above the V8 Hyper Kernel. It models framework and capability
topology, bounded registries, compatibility, policy-aware assessments, health,
diagnostics, lifecycle, and advisory change plans.

It does not contain executors. Adaptation and change-plan artifacts have an
immutable `executable = false` marker. “Planning Reference” and “Approved
Reference” are lifecycle labels only.

## Topology, registry, discovery, and dependencies

Framework and capability nodes are immutable references. Edges may describe
dependency, compatibility, governance, health, event, configuration, security,
observability, ownership, or interface relationships. Node and edge counts are
bounded. Dependency diagnostics deterministically report missing references,
cycles, and version conflicts.

The framework registry includes references for all 11 V8 components, all 15 V7
frameworks, V6 TikTok AI centers, and future V9 records. Discovery queries only
explicit in-process registries: there is no filesystem scan, remote discovery,
external registry, broker, or network call.

## Contexts and adaptation metadata

Contexts are frozen tenant/workspace/namespace-scoped metadata with bounded time
ranges and secret-safe metadata. Adaptation profiles contain references to
current and proposed states, triggers, policies, constraints, compatibility,
risks, evidence, review, approval, change plans, limitations, and audit.

Policy-aware assessment reads references to V8 Hyper Governance, V7 runtime
governance/security/configuration, and V6 governance/risk centers. Pause,
maintenance, and kill-switch signals make an assessment ineligible. They never
cause runtime action.

## Compatibility and version negotiation

Declared read-only adapter paths cover V6→V7, V7→V8, V8→V9, and V6→V9.
Negotiation is bounded, deterministic, and explainable. It reports selected and
fallback references and conflicts. It never migrates configuration, storage,
contracts, APIs, dashboards, OpenAPI, or extensions.

## Change planning and validation

Change plans describe dependency, compatibility, security, governance, health,
configuration, and observability impact by reference. They may carry rollback,
validation, review, approval, risk, confidence, limitation, version, and audit
metadata. No apply or mutation operation exists.

Validation covers reference and metadata integrity, dependencies, topology,
contexts, safe metadata, scopes, time ranges, node/edge counts, and result
limits. Diagnostics and health are read-only projections.

## Security and safety

V9 enforces tenant, workspace, and namespace isolation; read-only permissions;
source boundaries; secret filtering; bounded assessments; and local-only
discovery. Passwords, API keys, tokens, cookies, sessions, and proxy credentials
are redacted from projections.

There is no arbitrary code, policy, or adaptation execution; no configuration
apply; no workflow or scheduler mutation; no resource allocation; no service
restart; no recovery, snapshot, rollback, or migration execution; and no TikTok,
browser, account, device, proxy, publishing, outreach, bypass, or spam action.

## API and dashboard

All `/v9/kernel` routes are GET-only. They project kernel metadata, registries,
topology, dependencies, contexts, adaptations, policy and constraint references,
compatibility, version negotiation, change plans, validation, diagnostics,
health, metrics, audit, and lifecycle. No write, automatic approval/adaptation,
mutation, apply, execute, migration, or secret-value route is defined.

The dashboard projection exposes the same data without actions.

## Operations and Windows local guide

From PowerShell in `C:\Users\laow7\Documents\TKAI`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v9\adaptive_meta_kernel -q
.\.venv\Scripts\python.exe -m ruff check src\tkai\v9 tests\v9
.\.venv\Scripts\python.exe -m mypy src\tkai\v9
```

The feature is embedded by `server.api.app.create_app`; it opens no sockets by
itself and needs no live TikTok access, account, browser, proxy, cloud service,
external registry, or network connection. Operational response is limited to
inspecting GET projections and pausing upstream activity through the existing
governed V6–V8 controls. V9 itself never changes runtime state.
