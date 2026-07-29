# Lifecycle

The lifecycle is Created, Initialized, Ready, Running, Paused, Recovering,
Stopping, Stopped, Archived, and Deleted. `LIFECYCLE_TRANSITIONS` is the
deterministic transition graph. Deleted is terminal. State changes use optimistic
version checks; illegal or stale transitions fail without mutation. Explicitly
registered compatibility edges may bridge versioned legacy state names.
