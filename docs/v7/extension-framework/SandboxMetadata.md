# Sandbox Metadata

Sandbox metadata describes policy plus capability, permission, resource,
event, state, and configuration boundaries. `executable_runtime` is always
false and a true value is rejected.

This is not a process sandbox, interpreter, container, import hook, or security
runtime. Operational enforcement remains with the existing TKAI security,
RBAC, tenant, workspace, and runtime layers.
