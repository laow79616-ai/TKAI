# Hyper Intelligence Security

Read access is RBAC compatible and is constrained by tenant, workspace, and
knowledge namespace. `intelligence_viewer`, `intelligence_auditor`, and
`administrator` roles provide the reference permission model. Integrators may
map these permissions into the existing platform identity system.

Likely secrets are recursively redacted during ingestion and observability.
Audit records capture metadata registration and aggregation. Never place
credentials, evidence payloads, chain-of-thought, or hidden reasoning in
metadata.
