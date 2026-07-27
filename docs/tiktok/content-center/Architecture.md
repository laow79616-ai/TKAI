# TikTok AI Content Center

## Architecture

The Content Center is the TikTok Cloud Control Platform's tenant-scoped content
control plane. It owns project metadata, media references, drafts, captions,
hashtags, covers, templates, schedules and publish queue state. It delegates
identity to TikTok Account Center, browser actions to TikTok Browser Runtime,
network routing to TikTok Proxy Center and account safety policy to TikTok AI
Account Farming. Workflow, automation, audit, metrics and observability remain
shared platform capabilities; this package does not replicate them.

## Lifecycle

Projects move through Draft, Editing, Ready, Queued, Scheduled, Publishing,
Published, Paused, Archived and Deleted using an explicit transition map.
Transitions increment versions and emit audit records. Deleted records are
excluded from normal project listings.

## Media Library

Videos, images, audio, subtitles and thumbnails are grouped by folder and tags.
Only `kms://` or `vault://` encrypted storage references are accepted. Binary
content is not stored by this service. A checksum is unique within a tenant and
workspace: repeated uploads return the existing asset and never duplicate
storage.

## Drafts

Drafts support create, edit, duplicate, archive, restore, immutable version
history, review state and approval state. Each edit records its actor and
timestamp. Publishing enforces approved state when approval enforcement is on.

## Captions

Captions may be manual, AI-generated or template-based. They support variables,
locale, character counting and configured length validation. AI generation is a
bounded upstream capability; generated output enters the same review flow.

## Hashtags

Hashtags may be manual or suggested, favorited and organized into collections.
Values must be unique, begin with `#`, and remain within TikTok's bounded count.
Ranking data is referenced, not copied from analytics infrastructure.

## Cover Management

Covers support encrypted upload references, normalized crops, previews through
the media layer, templates, reference history and approval state.

## Publishing Queue

Immediate and scheduled jobs have bounded priority, retries and backoff. Queue
processing honors the configured workspace concurrency limit. Cancellation is
available before execution. Failure reasons contain exception types rather than
secrets or sensitive upstream detail. Account, proxy, farming-policy and browser
ports are checked before completion.

## Schedules

One-time and recurring schedules record timezone, calendar reference, publishing
window and missed-run policy. One-time entries require an instant; recurring
entries require a recurrence expression. Workflow and Automation own triggering.

## Templates

Caption, hashtag, publishing and project templates support import, export and
clone. Template payloads are scoped and versioned. Export returns control-plane
data only and never media bytes or credentials.

## Analytics

Analytics exposes publishing history, queue statistics, success and failure
rates, latest processing time and content inventory. Metrics are:
`tiktok_content_projects_total`, `tiktok_media_assets_total`,
`tiktok_drafts_total`, `tiktok_publish_queue_total`,
`tiktok_publish_success_total`, `tiktok_publish_failures_total`, and
`tiktok_publish_latency_seconds`.

## Security

Every operation checks tenant and workspace boundaries and an RBAC permission.
Publishing requires approval. Media and cover fields accept encrypted references
only. Audit events contain action, opaque resource ID, actor and scope; payloads,
tokens and credentials are excluded. API hosts should reuse platform
authentication, rate limiting, audit sinks and observability middleware.

## Operations Guide

Monitor `/tiktok/content/metrics`, queue failures and publish latency. Pause
upstream account farming or automation before incident recovery. Retry only
bounded failed jobs after Account Center, Browser Runtime and Proxy Center are
healthy. Back up metadata through the platform data layer and encrypted objects
through the configured storage provider. Never copy raw media into logs.

API collections are rooted at `/tiktok/content`: `projects`, `media`, `drafts`,
`uploads`, `publishing`, `schedules`, `templates`, `analytics`, `dashboard` and
`metrics`.
