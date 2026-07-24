# TKAI Platform Enterprise 1.0 General Availability Preparation

## Release status and version mapping

Platform Enterprise 1.0.0 is prepared for general-availability review on the
Enterprise release branch. It is a platform composition, not a second Python
distribution: the published `tkai` package remains version `1.3.0`.

| Layer | Version | Status |
| --- | --- | --- |
| Runtime | 1.3.0 | GA ready |
| SDK | 2.0 | GA ready |
| Studio | 2.1 | GA ready |
| Enterprise | 3.0 | GA ready reference foundations |
| Platform Enterprise | 1.0.0 | GA preparation complete |

## Included layers

- Runtime 1.3.0 provides backward-compatible workflows, providers,
  configuration, diagnostics, and optional local-first infrastructure.
- SDK 2.0 provides explicit Agent, Workflow, Tool, Provider, Memory, and
  Plugin contracts with deterministic reference implementations.
- Studio 2.1 provides a frozen local REST contract and reference frontend,
  workflow designer, execution monitor, and agent chat product layers.
- Enterprise 3.0 provides offline identity, organization, tenant,
  authorization, audit, and license reference contracts.

## Compatibility

Runtime public APIs, SDK contracts, Studio REST API, and their default behavior
remain unchanged. Enterprise contracts are additive, explicit, and do not
install middleware, hooks, providers, authentication, or enforcement.

## Validation summary

- Full offline pytest, Ruff, Black, Mypy, and `git diff --check` gates pass.
- Runtime, SDK, Studio, and Enterprise RC packaging, fresh-install, and
  release-validation suites have passed on their respective release baselines.
- Enterprise packaging validates wheel/sdist contents and isolated imports for
  Identity, Organization, Tenant, Authorization, Audit, and License packages.

## Installation, upgrade, and rollback

Install the one published distribution with `python -m pip install tkai`; see
[Installation](../Installation.md). Upgrade with a pinned environment, validate
`tkai version show` and offline Doctor output, then switch host traffic. Roll
back by restoring the prior pinned package and host configuration. No
TKAI-managed data migration exists because reference stores are local memory.

## Operations

Use `tkai doctor` and `tkai ai doctor --json` for offline diagnostics. Studio
and Enterprise services require explicit host integration; no service starts,
network connection opens, or credential is read merely by importing a package.
See [Operations](../OperationsGuide.md).

## Known limitations

- No Enterprise authentication, persistence, billing, enforcement, cloud, or
  marketplace capability.
- No production Studio authentication, durable multi-user storage, WebSocket
  monitoring, or bundled frontend build output.
- No automatic ProviderManager takeover, active provider health probing,
  distributed synchronization, or real external provider requirement.

## Manual release steps

1. Obtain release approval.
2. Push and merge the approved release branch.
3. Create and push the approved annotated release tag.
4. Create a release record and publish artifacts only when separately approved.

This preparation does not create a tag, push a branch, publish artifacts, or
start Cloud or Marketplace work.
