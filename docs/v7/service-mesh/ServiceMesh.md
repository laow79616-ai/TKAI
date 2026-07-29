# Service Mesh

A service descriptor contains its service ID, name, description, semantic
version, owner, category, dependencies, interfaces, reference-only endpoints,
health, metrics, audit history, lifecycle history, status, and secret-filtered
metadata.

The mesh is intended only for TKAI-internal composition. Endpoint references are
opaque identifiers such as `service://catalog/read`; the router never opens a
socket or invokes an external platform. Existing V6 services can remain outside
the mesh and retain their current behavior.
