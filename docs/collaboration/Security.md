# Security

Every operation uses a tenant, workspace, and actor scope. RBAC permission
validation precedes mutations and reads. Resource access validates tenant and
workspace identity, and every material action is recorded in the immutable
audit stream and activity timeline. APIs never infer cross-workspace access
from resource IDs.
