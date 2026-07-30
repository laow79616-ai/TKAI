# Hyper Knowledge Security

Access is GET-only and requires `knowledge:read`. RBAC-compatible reader,
reviewer, and administrator roles are accepted for metadata reads only.
Tenant, workspace, and knowledge scopes are independently checked. Common
secret-bearing keys and payload keys are recursively redacted from fabric
metadata, logs, traces, and audit projections.
