# Hyper Reasoning Fabric

The Hyper Reasoning Fabric standardizes reasoning coordination metadata across
TKAI V6, V7, and V8. `HyperReasoningFabric` registers immutable reasoning
profiles, safe summaries, evaluations, confidence, evidence, knowledge
references, advisory recommendations, explanations, and compatibility records.

All recommendations are advisory and expose `execution_authorized = false`.
The fabric never executes TikTok actions, mutates runtime state, or authorizes
execution. Reasoning records contain summaries and references, not hidden
reasoning. Metadata keys associated with chain-of-thought, scratchpads, or
internal reasoning are rejected recursively.

The dashboard and API are projections over local metadata. They do not poll or
call referenced frameworks.
