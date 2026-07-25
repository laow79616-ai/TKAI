# TKAI Enterprise Identity Foundation

## Scope

The Enterprise Identity Foundation provides offline, immutable descriptors and
explicit provider boundaries for TKAI Enterprise V3.0. It is intentionally not
an authentication system and does not modify TKAI Runtime, SDK, Studio, Studio
REST, or Platform public APIs.

This Sprint implements no JWT, OIDC, OAuth2, SAML, LDAP, database, session
store, login flow, password handling, network access, or background thread.

## Architecture

```text
Explicit caller
    -> IdentityContext / IdentityPrincipal
    -> injected IdentityProvider
    -> IdentityRegistry (optional explicit lookup)

ReferenceIdentityProvider: deterministic local test/example implementation
```

No provider is created automatically. `IdentityFactory` only builds the
explicitly requested `ReferenceIdentityProvider` for tests and examples.

## Identity Model

`IdentityPrincipal` supports five explicit kinds:

- `anonymous`
- `system`
- `service`
- `user`
- `bot`

An `IdentityAccount` links a principal to a provider identifier. `Credential`
is a safe reference containing an identifier, kind, optional fingerprint, and
metadata only; it cannot hold a secret, password, token, or raw credential.

`IdentityContext` carries a principal plus optional request and correlation
identifiers. It is explicitly constructed and never reads environment state,
web requests, or ContextVars.

## Claims and Role Mapping

`IdentityClaim` describes non-secret claim data. `RoleMapping` is a
declarative claim-to-role model with `applies_to`; it does not evaluate or
enforce RBAC policies. `IdentityGraph` provides an immutable snapshot of
identity relationships for descriptions and tests, not a persistent graph
database.

## Provider Boundary

`IdentityProvider` exposes only:

- `descriptor`
- `resolve(principal_id)`
- `capabilities()`

`IdentitySession` is a Protocol reserved for a future explicit adapter. This
foundation neither creates nor persists sessions.

`IdentityRegistry` is an in-process, thread-safe registry for caller-injected
providers. It contains no default provider and has deterministic listing and
capability matching.

## Reference Identity

`ReferenceIdentityProvider` is a deterministic in-memory implementation for
tests and examples. It resolves only supplied principals, has no environment
or network access, and raises `IdentityNotFoundError` for absent references.
It is not a production authentication implementation.

## Compatibility and Limitations

- Runtime, SDK, Studio, and the frozen Studio REST contract remain unchanged.
- No hidden identity provider, network request, environment read, persistence,
  session creation, login, or authentication protocol is enabled.
- No RBAC enforcement, tenant integration, repository, or cloud integration is
  provided.
- Future identity adapters must be explicitly injected and retain these safe
  boundaries.
