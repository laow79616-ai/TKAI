# Adaptive Planning Mesh Architecture

The TKAI V9 Adaptive Planning Mesh is a metadata-driven federation layer for
planning information from V9 components, V8 and V7 frameworks, and V6
planning-related centers. It contains immutable contracts, scope-aware local
registries, bounded allowlisted federation, read projections, and observability.

The mesh is advisory and read-only. It does not execute TikTok actions, mutate
runtime state, allocate or reserve resources, mutate schedulers, approve
execution, or trigger workflows. Every API route uses GET.

Data flows from local reference metadata through validation and secret filtering
into isolated registries, then into API and dashboard snapshots. Federation
stores references only and never discovers remote systems or changes an upstream
component.
