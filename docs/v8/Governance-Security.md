# V8 Governance Security

The security adapter provides RBAC-compatible read checks for
`governance:read`. Tenant and workspace coordinates must match the requesting
principal. Capability, framework, module, extension, and configuration
coordinates remain visible as boundary metadata for downstream compatibility.

Keys containing common secret markers such as password, token, credential,
secret, or API key are redacted when fabric metadata is created. Registration
and aggregation generate audit records. No security API grants runtime
capabilities.
