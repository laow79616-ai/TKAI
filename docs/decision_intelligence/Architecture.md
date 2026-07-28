# Decision Intelligence Architecture

The platform is a framework-neutral control plane organized around decisions,
contexts, objectives, alternatives, constraints, evaluations, recommendations,
approvals, explanations, simulations, and insights.

`DecisionIntelligencePlatform` owns domain orchestration and deterministic
reference algorithms. `DecisionIntelligenceAPI` exposes tenant-scoped read
resources, while adapters may persist records or integrate external reasoning,
evidence, workflow, event-streaming, digital-twin, and model services.

All records carry tenant and workspace scope. Mutations require explicit RBAC
permissions and append immutable audit entries. The package has no dependency
on the preserved TKAI platforms and therefore composes with them without
changing their contracts.
