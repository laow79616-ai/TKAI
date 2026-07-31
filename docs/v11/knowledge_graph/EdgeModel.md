# Edge Model

A `GraphEdge` identifies a source node, target node, relationship, provenance,
safe metadata, and scope. Construction rejects duplicate IDs and unknown
endpoints.

Relationships are depends-on, references, compatible-with, governed-by,
trusted-by, verified-by, derived-from, related-to, protected-by, and observed-by.
They express metadata semantics only and never establish an execution order.
