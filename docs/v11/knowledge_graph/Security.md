# Security

Every profile, node, and edge is checked against tenant, workspace, and namespace
scope. Secret-bearing metadata keys are rejected at construction and filtered
again during serialization. Existing RBAC-compatible hosting boundaries remain
applicable.

The service is local-first and exposes no hidden reasoning, credentials, runtime
mutation, graph mutation, execution, browser control, TikTok action, scheduling,
storage mutation, deployment, or service-control capability.
