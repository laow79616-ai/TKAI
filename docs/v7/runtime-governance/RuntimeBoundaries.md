# Runtime Boundaries

Boundary metadata covers tenant, workspace, capability, module, extension,
configuration, event, and service isolation. Runtime references may bind only
to boundaries in the exact same tenant, workspace, and namespace. Cross-scope
lookups fail closed. Boundaries describe expectations and do not enforce or
change a live runtime.
