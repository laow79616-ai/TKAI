# Unified Security and Policy Framework Architecture

`tkai.v7.security_framework` centralizes immutable policy, principal, role,
permission, scope, secret-reference, audit, compliance, health, and metric
contracts. The in-process `SecurityFramework` owns deterministic registries and
read-only projections. It makes no network calls, launches no runtime, and does
not alter TikTok business behavior.

Authorization is deny-by-default. Tenant and workspace checks run before RBAC;
capability and service boundaries run before policy evaluation. Policy priority
is deterministic and equal-priority allow/deny conflicts resolve to deny.

All decisions are reference-only metadata. The framework can advise and enforce
at integration boundaries, but it does not introduce a remote security service.
