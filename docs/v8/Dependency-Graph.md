# V8 Coordination Dependency Graph

The graph supports framework, capability, relationship, compatibility,
lifecycle, and health edges. Every edge is a reference. The graph provides
deterministic adjacency snapshots and cycle diagnostics.

There is deliberately no execution graph or execution edge type. Consumers
must not infer ordering, dispatch authority, or permission to run actions from
an edge.
