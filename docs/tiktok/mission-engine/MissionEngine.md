# Mission Engine

Approved missions enter a priority queue with a workspace, dependency list,
risk state, and timezone-aware execution window. Lower numeric priority runs
first. A mission becomes dispatchable only when approval is approved, risk is
clear, the execution window is active, dependencies are complete, and all
integrated services are healthy.

States are queued, dispatching, running, paused, recovering, completed, failed,
and rolled back. Audit events describe state changes without including mission
payloads or credentials.
