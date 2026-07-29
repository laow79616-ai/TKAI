# Compatibility

Compatibility checks semantic platform constraints, required platform
capabilities, interface names and semantic versions, dependency versions and
capabilities, and scope isolation. Results explain each failed dimension.
Migration metadata is advisory and `v6_compatible` defaults to true.

Supported version clauses are exact, `==`, `>=`, `<=`, `>`, `<`, compatible
minor (`~`), compatible major (`^`), comma-separated intersections, and `*`.
