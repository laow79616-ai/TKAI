# Governance Model

A governance profile binds tenant, workspace, namespace, owner, version,
lifecycle, policy references, constraint references, runtime references, health,
metrics, audit, and bounded secret-safe metadata.

Lifecycle values are draft, registered, validating, ready, review,
approved-reference, paused, maintenance, archived, and deleted.
`approved-reference` means only that metadata has an approval reference; it
never grants execution authority.
