# Security

The framework supports deny-by-default V7 RBAC and tenant, workspace, and owner
isolation. Dependencies may not cross scope. Secret-like keys are recursively
redacted from metadata, logs, traces, and audit details. APIs are GET-only.
