# TKAI V8 Hyper Kernel Architecture

TKAI V8 adds an execution-independent coordination layer above existing V6 and
V7 surfaces. The Hyper Kernel stores typed metadata and references; it does not
execute plans, dispatch events, invoke providers, or perform TikTok actions.

The composition root owns framework, capability, runtime, module, extension,
compatibility, and diagnostics registries. Discovery, dependency graph, health,
and diagnostics services read those registries. Security and observability are
cross-cutting and secret-filtered. Existing V6/V7 imports remain unchanged.

All Feature-1 state is in-memory and opt-in. Registry records are immutable and
tenant-, workspace-, and framework-scoped. Future persistence or execution
integrations must remain behind contracts and are outside Feature-1.

Feature 2 adds `tkai.v8.hyper_coordination` as an additive layer above the
kernel. It owns immutable coordination profiles, framework descriptors,
reference graphs, synchronization plans, governance evidence, diagnostics,
and read-only projections. It neither changes Feature-1 composition nor
imports an executor. Approved references remain advisory.
