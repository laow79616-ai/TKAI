# Security

Exact tenant, workspace, and namespace matching isolates extensions, plugins,
and dependencies. Parent-child references cannot cross scopes. Permissions
are restricted to a small internal read-only allowlist compatible with
external RBAC decisions.

Serialization redacts values whose keys resemble secrets, credentials, tokens,
cookies, passwords, API keys, or private keys. Audit and tracing records contain
references only. There is no arbitrary code execution, remote discovery,
package installation, secret retrieval, or TikTok business action.
