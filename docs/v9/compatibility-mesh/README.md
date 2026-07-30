# TKAI V9 Adaptive Compatibility Mesh

The Adaptive Compatibility Mesh is a metadata-driven, advisory, read-only
framework for describing compatibility across TKAI V6, V7, V8, and V9.

It provides immutable profiles, references, compatibility records,
assessments, matrices, recommendations, reviews, approvals, bounded local
federation, diagnostics, health, metrics, audit projections, and GET-only API
metadata.

## Safety boundary

The mesh:

- preserves V6, V7, and V8 compatibility through references only;
- does not change TikTok business behavior;
- exposes no execution endpoints;
- does not mutate runtime state or upstream frameworks;
- does not automatically migrate or upgrade;
- does not execute rollback;
- does not apply configuration;
- does not mutate schemas or storage;
- does not install plugins;
- does not execute deployments; and
- rejects secret-bearing metadata.

All API routes are under `/v9/compatibility/` and support `GET` only.
