# Marketplace Server V6 Architecture

Marketplace Server is a separate, reference-only product layer. Its planned
boundaries are Server → REST API contracts → application services → domain
models → storage protocols → infrastructure. Sprint-1 implements only
immutable contracts and local reference services; it starts no server, network,
database, or background worker.

## Registry Foundation

Sprint-2 adds an isolated, reference-only Registry domain under
`server.registry`. It layers immutable Registry models over a `RegistryStorage`
protocol, a thread-safe `ReferenceRegistryStorage`, and an explicitly injected
`ReferenceRegistryService`. The foundation records deterministic sequence-based
events and performs no HTTP, network, filesystem, database, artifact, or
background-worker activity.

## Publisher Foundation

Sprint-3 adds an isolated, reference-only Publisher domain under
`server.publisher`. It uses immutable Publisher contracts, an explicit
`PublisherStorage` protocol, thread-safe `ReferencePublisherStorage`, and an
injected `ReferencePublisherService`. It is independent of both
`server.registry` and `marketplace.publisher`, and introduces no account,
authentication, authorization, HTTP, network, database, artifact, or worker
behavior.

## Package Foundation

Sprint-4 adds an isolated, reference-only Package domain under
`server.package`. It uses immutable Package contracts, an explicit
`PackageStorage` protocol, thread-safe `ReferencePackageStorage`, and an
injected `ReferencePackageService`. It is independent of Server Registry,
Server Publisher, and `marketplace.package_catalog`, with no HTTP, network,
database, artifact, account, or worker behavior.
