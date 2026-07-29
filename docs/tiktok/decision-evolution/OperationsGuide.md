# Decision Evolution Center Operations Guide

Run the center inside the existing TKAI API process. Verify source adapters are
read-only, use tenant/workspace-scoped service credentials, and enforce a maximum
366-day time range and 500-result response unless a smaller local policy applies.

Before analysis, confirm workspace and account pause state, kill-switch state,
restriction/challenge state, governance policy, risk policy, and evidence integrity.
Paused, restricted, challenged, or policy-blocked inputs may be analyzed as
historical references but must never trigger an operation.

Review analysts should inspect the complete score breakdown, source references,
missing evidence, calibration difference, and causal wording. Marking an analysis
as Approved Reference only confirms the record. Operational approval remains in
the originating governed workflow.

Monitor the ten `tiktok_decision_evolution_*` metrics and the shared API audit log.
Unexpected source volume, out-of-scope records, secret-shaped metadata, invalid
integrity references, or write attempts should fail closed and be investigated.

Back up records using existing TKAI backup facilities. Restore history and version
records together so supersession references remain valid. No Decision Evolution
procedure requires live TikTok access.
