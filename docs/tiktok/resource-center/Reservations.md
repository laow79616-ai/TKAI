# Reservations

Reservations contain an ID, owner, start time, expiration, heartbeat, and priority.
Only available resources can be reserved, providing deterministic conflict
detection. Heartbeats renew bounded expiration, cancellation releases the resource,
and cleanup expires abandoned reservations automatically.
