# Security

Every resource carries tenant and workspace identity. Service methods enforce
both before reads or mutations. RBAC permissions are `tiktok:data:read`,
`tiktok:data:write`, `tiktok:data:execute`, and `tiktok:data:storage`; the
`tiktok:data:admin` permission covers all four.

Audit entries record action, resource, operator, tenant, workspace, and time.
Dataset and storage references must be encrypted-reference URIs. Secret-like
metadata keys are rejected, and job failures record exception classes only.

The module is designed exclusively for authorized TikTok Cloud Control Platform
operations. It does not implement unauthorized access, restriction or CAPTCHA
bypass, evasion, scraping circumvention, or other social-platform modules.
Deployments must retain TikTok terms, privacy, consent, data minimization,
retention, and regional-policy controls.
