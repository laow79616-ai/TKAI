# Quota

Tenant- and workspace-scoped quotas can bound requests, tokens, concurrency, and
rate. Rejections occur before provider invocation and increment
`model_quota_rejections_total`. Production hosts may provide windowed distributed
rate accounting while preserving this contract.
