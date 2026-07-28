# Leases

Every allocation creates an owner-bound lease. Durations and renewals are bounded.
Renewal validates tenant, workspace, owner, active state, and expiration. Cleanup
deactivates expired leases, closes their allocations, and releases their resources.
Operators should run reconciliation on startup and periodically thereafter.
