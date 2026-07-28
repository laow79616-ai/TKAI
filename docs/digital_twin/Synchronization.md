# Synchronization

Synchronization policies support manual, scheduled, and event-driven modes,
optimistic conflict detection, bounded retry configuration, and consistency
validation. State updates carry an expected version. A mismatch records a failed
sync metric and audit event; successful updates create an immutable snapshot.
