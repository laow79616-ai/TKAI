# Lifecycle

Profiles move through guarded transitions: Draft to Training, Training to
Learning, Learning to Ready, Ready to Running, Running to Paused or Completed,
Completed to Archived, and Archived to Deleted. Paused profiles may resume
training, learning, or running. Invalid or destructive shortcuts are rejected
and every accepted transition is audited.
