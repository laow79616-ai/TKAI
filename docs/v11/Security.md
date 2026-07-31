# Security

All projections are local-first and safe-metadata-only. Tenant, workspace, and
namespace equality enforce isolation. Secret-bearing keys are rejected on input
and redacted on output. RBAC compatibility is preserved at the transport layer.
Runtime mutation, storage mutation, scheduling, deployment, service control,
browser control, TikTok actions, and hidden-reasoning exposure are disabled.
