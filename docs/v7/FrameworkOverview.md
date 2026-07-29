# V7 Framework Overview

| Framework | Responsibility | Production boundary |
| --- | --- | --- |
| Foundation | contracts, kernel, lifecycle, registries | opt-in composition |
| Capability | capability metadata and dependency validation | no provider execution |
| Service Mesh | service discovery and routing metadata | read-only projection |
| Event Fabric | event contracts, delivery metadata, replay plans | no external broker required |
| State | scoped state metadata, transitions, recovery simulation | no implicit persistence |
| Workflow | definitions, validation, orchestration plans | no execution endpoint |
| Resource | catalog, capacity, reservations, recovery plans | no infrastructure mutation |
| Security | RBAC, policy, isolation, redaction, audit | deny by default |
| Observability | metrics, logs, traces, health, diagnostics | secret-filtered |
| Configuration | sources, precedence, validation, snapshots | no automatic mutation |
| Extension | packages, plugins, validation, sandbox metadata | no automatic loading |
| AI | providers, models, prompts, governance, evaluation | no model execution |
| Data | storage and repository metadata, transactions, retention | adapter-neutral |
| Intelligence | evidence, decisions, reviews, recommendations | no autonomous action |
| Runtime Governance | eligibility, approvals, pause and kill-switch metadata | no runtime control endpoint |

The machine-readable catalog is `FRAMEWORK_MANIFEST.json`. All framework
registries use unique identifiers and bounded, deterministic projections.
