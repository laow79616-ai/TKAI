# Graph Architecture

`GraphProfile` owns immutable node, edge, taxonomy, ontology, provenance, lineage,
validation, audit, scope, and safe-metadata registries. `AutonomousKnowledgeGraph`
validates the snapshot and provides pure projections. API and dashboard adapters
serialize those projections without adding behavior.

All defaults are tuples, frozen dataclasses, enums, or read-only mappings. Output
ordering follows declaration order and sorted diagnostic/count keys, producing the
same projection for the same profile.

The graph deliberately has no traversal engine, database, cache, background job,
plugin execution, inference engine, or optimizer.
