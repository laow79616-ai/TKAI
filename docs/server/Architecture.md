# Marketplace Server V6 Architecture

Marketplace Server is a separate, reference-only product layer. Its planned
boundaries are Server → REST API contracts → application services → domain
models → storage protocols → infrastructure. Sprint-1 implements only
immutable contracts and local reference services; it starts no server, network,
database, or background worker.
