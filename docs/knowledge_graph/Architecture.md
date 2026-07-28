# Enterprise AI Knowledge Graph Architecture

The platform is a framework-neutral control plane beneath `knowledge_graph/`.
Its typed domain model owns graphs, entities, edges, ontologies, taxonomies,
schemas, provenance, and lineage. Every operation is explicitly tenant and
workspace scoped. The API facade exposes read projections under
`/knowledge-graph/*`; the FastAPI server and Prometheus endpoint compose it with
the existing TKAI platforms without changing their contracts.

Traversal, queries, inference, and analytics are deterministic and bounded.
External databases, text indexes, and vector systems integrate through
references and adapters rather than becoming core runtime dependencies.
