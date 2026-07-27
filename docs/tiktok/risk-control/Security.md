# Security

- Every operation enforces tenant and workspace isolation and risk-specific RBAC.
- Policy, rule, threshold, time-window, concurrency, rate, and recovery values are validated and bounded.
- State-changing non-critical actions require an approved, unexpired review. Critical action handling is auditable and fail-closed.
- Evidence uses opaque references. Metadata rejects secret, token, cookie, session, password, and credential keys.
- Cookies, sessions, proxy credentials, and other secrets are never accepted as risk payloads or written to logs.
- Recovery cannot continue while a TikTok challenge or restriction remains unresolved.
- All mutations append actor, scope, resource, action, and timestamp to the audit stream.
- The center provides policy enforcement only; it does not bypass CAPTCHA, platform restrictions, rate limits, identity controls, or TikTok security.
