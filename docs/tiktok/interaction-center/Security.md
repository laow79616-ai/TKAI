# Security

RBAC is checked before mutation or execution. Every resource read and write is
restricted to its tenant and workspace. Approved review of the current draft is
mandatory before queueing. Audit records omit content and secrets; metadata rejects
credential-like keys. No bulk messaging, manipulation, CAPTCHA handling, restriction
evasion, or platform-security bypass capability exists.
