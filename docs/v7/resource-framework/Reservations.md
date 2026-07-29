# Reservations

Reservations are reference-only planning records. Validation requires a
positive quantity, matching tenant/workspace scope, sufficient estimated
capacity, and URI-shaped external references when a reference is supplied.

Active, expired, and historical records are retained independently of runtime
systems. A reservation conflict reports the requested and estimated available
quantities plus conflicting record IDs. Expiring a record never releases or
stops a real resource because the framework never acquired one.
