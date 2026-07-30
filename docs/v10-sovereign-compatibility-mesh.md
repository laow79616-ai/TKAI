# TKAI V10 Sovereign Compatibility Mesh

This mesh is a local-first deterministic compatibility index for completed TKAI
V6–V10 components. It uses immutable metadata, bounded registries, a fixed rule
vocabulary, secret-safe serialization, and GET-only projections.

It covers framework, capability, service, module, extension, runtime,
configuration, storage, contract, interface, schema, API, OpenAPI, Dashboard,
AI Studio, deployment, integrity, trust, governance, release, package, and
manifest references. V6–V9 historical metadata is never altered.

Negotiation and plans are advisory and reproducible. Integration with Sovereign
Core, Integrity Mesh, Trust Mesh, Governance Mesh, V9 meshes, and V6–V8
frameworks is reference-only. The mesh cannot execute contracts or policies,
load modules or extensions, access the network, control services, mutate runtime
state, apply configuration, migrate schemas or storage, deploy, approve,
upgrade, roll back, or perform browser, account, proxy, publishing, or TikTok
actions.

For local Windows validation:

```powershell
python -m pytest tests/v10/compatibility_mesh
python -m ruff check src/tkai/v10/compatibility_mesh tests/v10/compatibility_mesh
```
