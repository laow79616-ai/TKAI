# Policy Engine

Policies have an ID, type, scope, lifecycle, priority, rules, compatibility
versions, metadata, audit references, health, and metrics. Registration validates
required scope, rule permissions, and V7 compatibility. Evaluation considers
active policies only, orders them by descending priority and stable policy ID,
and resolves only the highest-priority matches.

No match denies. A highest-priority deny denies. Conflicting effects at the same
priority deny and emit conflict metrics. Evaluation is local and reference-only.
