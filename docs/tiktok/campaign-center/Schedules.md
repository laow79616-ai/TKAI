# Campaign Schedules

Schedules support Immediate, One-Time, Recurring, and Calendar modes. Each record
contains an IANA-style timezone and a positive execution window. One-Time requires
a start timestamp, Recurring requires a recurrence expression, and Calendar
requires an opaque calendar reference.

Schedules describe intent. Actual execution timing remains owned by the existing
scheduler, automation, workflow, publishing, and execution modules.
