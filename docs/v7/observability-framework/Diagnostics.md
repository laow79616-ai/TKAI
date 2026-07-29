# Diagnostics

Collectors cover health, dependency, configuration, validation, and recovery.
Collectors receive an exact tenant/workspace scope and must return read-only
results in that same scope. Diagnostics inspect and recommend; they never
mutate configuration, dependencies, or recovery state.
