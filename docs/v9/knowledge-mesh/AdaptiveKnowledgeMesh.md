# TKAI V9 Adaptive Knowledge Mesh

## Architecture

The Adaptive Knowledge Mesh is a local, metadata-only federation layer for V6,
V7, V8, V9, and future bounded V9 components. It stores immutable references,
ontology and taxonomy descriptors, semantic relationships, evidence provenance,
lineage, versions, quality, confidence, compatibility, and governance metadata.
Upstream knowledge payloads remain in their owning components.

Federation adapters copy only bounded descriptors. The mesh performs no network
calls, graph execution, arbitrary transformations, automatic migration,
automatic approval, TikTok actions, browser actions, or runtime mutation.
`approved_reference` confirms an artifact reference only.

## Records, validation, and compatibility

Profiles bind tenant, workspace, namespace, domains, ontologies, taxonomies,
knowledge, evidence, relationships, lineage, compatibility, and governance
references. Sensitive material is reference-only. Safe metadata filtering
redacts cookies, sessions, proxy credentials, API keys, passwords, and secrets.
Compatibility is advisory and never triggers migration.

Quality scores are deterministic weighted evaluations with factors, weights,
supporting references, limitations, and an explanation. Confidence values are
bounded to `[0, 1]`. Validation bounds source counts, relationship counts,
lineage depth, time ranges, and result sizes. Lineage makes no unsupported
derivation or causal claims.

## Governance, security, and safety

Reads are RBAC-compatible and isolated by tenant, workspace, namespace, profile,
domain, ontology, entity, knowledge, and evidence scope. Pause, maintenance,
kill-switch, governance, retention, and security-policy metadata is awareness
only. All `/v9/knowledge/` routes are GET-only. There are no public write,
mutation, graph-query, execution, migration, approval, or secret routes.

## Operations and Windows local guide

Health, analytics, diagnostics, metrics, audit, lifecycle, and dashboard data
are read-only projections. Metrics use the `v9_knowledge_mesh_*` namespace.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v9\knowledge_mesh -q
.\.venv\Scripts\python.exe -m ruff check src\tkai\v9\knowledge_mesh
.\.venv\Scripts\python.exe -m mypy src\tkai\v9\knowledge_mesh
```

No TikTok credentials, accounts, browser, external service, database, or
network access is needed.
