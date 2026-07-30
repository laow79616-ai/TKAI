# TKAI V10 Sovereign Core Architecture

## Architecture and sovereign core

The Sovereign Core is a local-first, immutable-metadata coordination layer above
the V9 Adaptive Meta-Kernel. It provides bounded registries, reference topology,
trust and policy assessment metadata, deterministic compatibility negotiation,
diagnostics, health, audit, and advisory change plans. It has no executor,
runtime mutator, remote control plane, network discovery, or secret retrieval.

## Trust domains, identities, and principals

Trust domains bind tenant, workspace, and namespace scope to identity, principal,
policy, boundary, integrity, attestation, and compatibility references.
Principals are local references for users, services, frameworks, capabilities,
modules, extensions, runtimes, systems, tests, and mocks. No identity provider,
credential, authentication service, or remote verifier is embedded.

## Integrity and attestations

Integrity records describe expected hashes, observed-hash references, evidence,
verification state, time, version, and audit references. Attestations are
immutable, locally issued metadata. Registration never performs verification or
creates an attestation automatically; secret-bearing evidence is forbidden.

## Sovereign boundaries and local control plane

Boundaries express allowed and restricted references within host, tenant,
workspace, namespace, framework, capability, service, module, extension,
configuration, storage, event, state, runtime, API, dashboard, and AI Studio
scopes. The control-plane projection is coordination metadata only and exposes
no operational endpoint.

## Registries, discovery, topology, dependencies, and contexts

Registries cap records and result sizes and isolate tenant/workspace/namespace
keys. Discovery queries only registered local metadata. It never scans a
filesystem or calls a network. Topology caps nodes and edges and is
non-executable. Validation detects missing/circular dependencies, version
conflicts, integrity gaps, and attestation gaps. Context time ranges are bounded.

## Policy evaluation and compatibility negotiation

Policy evaluation consumes read-only references to V6-V9 governance/security
surfaces and reports eligibility, review, approval, audit, pause, maintenance,
and kill-switch awareness. It cannot execute a policy. Negotiation is
deterministic for V6, V7, V8, and V9 consumers and contracts through runtime and
deployment metadata. It never migrates, upgrades, or rolls back.

## Change planning, validation, diagnostics, and health

Change plans record impacts, rollback references, validation/review/approval
references, risks, confidence, and limitations. They cannot be applied.
Validation and diagnostics are read-only bounded projections. Health exposes
readiness and liveness without starting, stopping, restarting, recovering, or
allocating anything.

## Security and safety

Scope checks enforce tenant, workspace, and namespace isolation. Safe metadata
rejects secret-shaped keys and serialization redacts passwords, cookies,
sessions, proxy credentials, API keys, secrets, and tokens. The architecture
performs no arbitrary code/policy/attestation execution, external calls,
unrestricted scans, TikTok actions, browser/account/device/proxy actions,
publishing, outreach, bypass, spam automation, configuration/storage/schema
mutation, workflow scheduling, recovery, or runtime mutation.

## Compatibility

V6-V9 adapters are read-only references. Existing APIs, TikTok behavior,
dashboard, AI Studio, local runtime, deployment, configuration, storage,
extension, security, and OpenAPI behavior remain unchanged. V10 adds a new
package and GET-only routes.

## Operations guide

Instantiate `SovereignCore`, register immutable records in an explicitly named
bounded registry, and query projections or diagnostics. Treat all lifecycle
states containing “reference” as labels only. Human review and existing
governance remain required for every operational decision.

## Windows local guide

From the repository root, use the project virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v10\sovereign_core
.\.venv\Scripts\python.exe -m ruff check src\tkai\v10 tests\v10
.\.venv\Scripts\python.exe -m mypy src\tkai\v10
```

These tests are offline and mock-only; they require no accounts, cookies,
sessions, proxies, browser, cloud service, or remote identity/attestation system.
