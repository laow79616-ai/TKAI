# API Lifecycle

Managed APIs move through Draft, Published, Deprecated, Suspended, Retired,
Archived, and Deleted states. Only valid transitions are accepted and only
Published APIs can receive gateway traffic. Every mutation is tenant/workspace
scoped and lifecycle changes are audited.
