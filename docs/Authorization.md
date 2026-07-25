# TKAI Enterprise Authorization Foundation

## Scope

Authorization Foundation is an offline Enterprise architecture layer. It adds
immutable RBAC descriptors, ABAC extension contracts, and explicit reference
evaluators only. It does not modify Runtime, SDK, Studio, Studio REST, Agent,
Workflow, or Provider behavior.

No authentication, JWT, OIDC, OAuth2, LDAP, SAML, database, persistence,
middleware, enforcement, audit, licensing, cloud, Kubernetes, or network
integration is implemented.

## Authorization Model

`AuthorizationContext`, `AuthorizationRequest`, `AuthorizationDecision`,
`AuthorizationExplanation`, and `AuthorizationCapability` are immutable
descriptors. Outcomes are `allowed`, `denied`, `not_applicable`, and
`indeterminate`. A caller decides what to do with a result; no request is
blocked or changed by this foundation.

## RBAC

`RoleDescriptor` declares permission identifiers. `PermissionDescriptor`
combines a `ResourceDescriptor`, `ActionDescriptor`, and optional
`ScopeDescriptor` values for organization, tenant, workspace, or another
caller-defined scope. Descriptors do not grant or enforce permissions.

## ABAC Extension

`Attribute`, `Subject`, `Resource`, `Environment`, and `PolicyExpression` are
extension contracts. There is no rule parser, expression evaluator, policy
engine, attribute lookup, or implicit runtime connection.

## Service and Reference Components

`AuthorizationService` declares explicit `evaluate`, `explain`,
`evaluate_many`, and `capabilities` methods. `ReferenceAuthorizationService`
performs deterministic comparison of caller-supplied role descriptors only.
`ReferenceRoleRegistry` and `ReferencePermissionRegistry` are thread-safe,
in-memory registries for tests and examples.

These reference results are not enforcement: no Runtime hook, SDK hook, Studio
middleware, REST middleware, or global policy is installed.

## Current Limitations

- No authentication or identity-protocol implementation.
- No RBAC enforcement and no ABAC rule engine.
- No persistence, database, ORM, cache, network, or background worker.
- No audit, license, cloud, Kubernetes, or automatic policy integration.
