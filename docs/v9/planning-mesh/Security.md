# Security

Only read and review RBAC actions are recognized. Tenant, workspace, and
planning scope must match. Secret-bearing metadata is rejected recursively and
all registry activity is audited. Execution, allocation, scheduler mutation,
workflow triggering, and automatic approval are prohibited.
