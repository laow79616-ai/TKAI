# Node Model

A `GraphNode` contains an ID, enum-backed kind, label, version, reference IDs,
taxonomy path, safe metadata, and tenant/workspace scope. It is frozen and always
has `executable = false`.

Twenty-one kinds cover framework, capability, module, service, extension,
configuration, runtime reference, API, dashboard, AI Studio, policy, constraint,
trust, integrity, compatibility, knowledge, reasoning, decision, planning,
operations, and recovery.
