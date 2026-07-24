# TKAI Marketplace V5 Publisher Foundation

## Scope

The Publisher Foundation is a local, reference-only Marketplace domain layer.
It provides immutable publisher declarations and a thread-safe in-memory
registry. It does not change Marketplace package registry behavior, Runtime,
SDK, Studio, Enterprise, Cloud, or Platform APIs.

No network, publisher account, package download, installation, verification
service, trust service, Cloud integration, or persistence is implemented.

## Publisher model

`Publisher` combines an explicit id with a `PublisherProfile`, optional
`PublisherOrganization`, capabilities, metadata, and one descriptive tier:

- Community
- Verified
- Official
- Enterprise

All descriptors are frozen and defensively copy metadata. The tiers describe
catalog information only; they grant no permission and enforce no behavior.

## Factory, registry, and policy

`PublisherFactory` constructs descriptors only from explicit caller inputs.
`PublisherRegistry` stores those descriptors in memory with stable snapshots
and thread-safe register, unregister, get, list, and clear operations.
`PublisherPolicy` returns declarative validity, warnings, and reasons; it does
not automatically register, reject, promote, or verify a publisher.

`ReferencePublisherService` composes the factory and registry for examples and
tests. Its `close()` clears caller-owned in-memory declarations and is
idempotent.

## Verification and trust boundaries

`PublisherVerification` and `PublisherTrust` are Protocols reserved for a
future explicit adapter. They make no network request, accept no certificate,
manage no key, evaluate no reputation, and do not affect package installation.

## Current limitations

- No publisher registration API, login, account, or organization lookup.
- No remote registry, search, package download, upload, or installation.
- No verification evidence, signature validation, trust score, or enforcement.
- No database, Cloud service, background worker, or hidden global state.
