# Agent Lifecycle

Definitions move through Draft, Created, Ready, Running, Paused, Completed,
Failed, Cancelled, and Archived states. Illegal transitions fail before state
changes. Runs retain immutable inputs, outputs, events, and metrics. Pause,
resume, and cancellation delegate cooperative execution control to the
existing workflow runtime when a workflow is attached.

