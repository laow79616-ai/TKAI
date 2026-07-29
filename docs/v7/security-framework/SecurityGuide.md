# Security Guide

Use least-privilege permissions, small composable roles, explicit tenant and
workspace assignments, and narrow capability/service scopes. Register explicit
policies for every granted operation and prefer a higher-priority deny for
emergency restrictions.

Never place credentials in policy metadata, conditions, logs, or configuration.
Use opaque secret references. Review compliance, conflicts, denied decisions,
rotation metadata, and audit history before release.
