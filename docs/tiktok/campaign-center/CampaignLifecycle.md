# Campaign Lifecycle

The supported lifecycle is:

`Draft → Planning → Review → Approved → Scheduled → Running → Completed → Archived → Deleted`

Planning can return to Draft, Review can return to Planning, Scheduled and Running
can pause, and Paused can resume or archive. Deletion is a soft-delete and is
allowed only from Draft, Planning, or Archived.

Review-to-Approved and Scheduled-to-Running transitions require an active,
unexpired campaign approval. Scheduling also requires at least one validated
campaign plan.
