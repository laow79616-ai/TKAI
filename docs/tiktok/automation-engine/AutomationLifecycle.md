# Automation lifecycle

The lifecycle is Draft, Review, Approved, Ready, Scheduled, Running, Paused,
Completed or Failed, Archived, and Deleted. Only declared transitions are
accepted. Approval promotion requires both `tiktok:automation:approve` and an
approved review record. Deleted records remain auditable but are not listed.
