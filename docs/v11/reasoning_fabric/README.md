# TKAI V11 Autonomous Reasoning Fabric

The Autonomous Reasoning Fabric is TKAI V11's local-first, immutable,
metadata-driven coordination layer over the Autonomous Intelligence Core and
Autonomous Knowledge Graph. It records bounded references to contexts, claims,
premises, evidence, inference classifications, assumptions, constraints,
alternatives, contradictions, confidence, uncertainty, safe explanations, and
advisory evaluations.

## Architecture and profile

`ReasoningFabricProfile` is a frozen metadata aggregate. Every collection is
tuple-backed, scoped, versioned, deterministic, and bounded by `FabricLimits`.
The fabric validates reference identifiers, safe metadata, evidence-provider
allowlists, confidence ranges, tenant scope, and collection counts. It performs
no arbitrary inference and exposes no mutation methods.

## Evidence and knowledge graph integration

Evidence is explicitly supplied as a read-only `EvidenceReference`; there is no
automatic ingestion, filesystem scan, external search, or network access.
V11 Knowledge Graph node, edge, relationship, taxonomy, ontology, provenance,
lineage, dependency, and validation identifiers remain references only. Graph
mutation and graph execution are disabled.

## Safe explanations, confidence, and uncertainty

Explanations contain only user-facing summaries and supporting metadata
references. Hidden chain-of-thought, private scratchpads, prompts, token traces,
system messages, secret-bearing context, and internal model traces are neither
accepted nor persisted. Confidence may omit a numeric value to avoid fabricated
precision. Uncertainty uses an explicit bounded classification.

## Compatibility and governance

Compatibility projections cover TKAI V6 through V11 without migration, upgrade,
recovery, or rollback. Governance, integrity, and trust integrations are
read-only references. Policy execution and automatic approval are disabled;
manual review, pause, maintenance, and kill-switch awareness are surfaced.

## Dashboard and API

The dashboard projection has 27 read-only sections and no actions. The HTTP
surface contains 27 GET-only routes rooted at `/v11/reasoning`. It includes no
write, execution, secret retrieval, hidden-reasoning, or graph-mutation route.

## Operations and Windows local guide

No service, deployment, browser, account, scheduler, runtime, configuration, or
storage operation is required. On Windows, from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v11\reasoning_fabric -q
.\.venv\Scripts\python.exe -m ruff check src\tkai\v11\reasoning_fabric
```

All tests are offline and mock-only.
