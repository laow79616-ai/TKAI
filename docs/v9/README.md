# TKAI V9 Architecture and Component Overview

V9 is a read-only adaptive metadata and advisory layer over the stable TKAI
V6-V8 platform. Its ten completed components are:

1. Adaptive Meta-Kernel Architecture
2. Adaptive Intelligence Mesh
3. Adaptive Governance Mesh
4. Adaptive Knowledge Mesh
5. Adaptive Reasoning Mesh
6. Adaptive Decision Mesh
7. Adaptive Planning Mesh
8. Adaptive Operations Mesh
9. Adaptive Recovery Mesh
10. Adaptive Compatibility Mesh

Every mesh provides scoped registries, compatibility metadata, diagnostics,
health, metrics, audit projections, and dashboard views. Components exchange
references rather than mutating foreign state. The aggregate API surface is
registered in `server.api.app`; V9 endpoints remain GET-only.

See `ADAPTIVE_META_KERNEL.md` for the kernel contract and the component
subdirectories for detailed architecture and operating guidance.
