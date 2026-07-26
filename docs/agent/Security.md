# Agent Runtime Security

Definitions declare least-privilege permission strings. Tool access is denied
unless the required permission is present. Workspaces and memory namespaces
are explicit inputs and no host path is accessed by the foundation. Create,
run, pause, resume, cancel, and delete actions produce instance-scoped audit
events. Authentication and tenant enforcement remain the host API's concern.

