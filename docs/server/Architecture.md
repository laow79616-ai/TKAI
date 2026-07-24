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
