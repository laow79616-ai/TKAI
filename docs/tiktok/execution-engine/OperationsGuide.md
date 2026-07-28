# TikTok AI Execution Engine Operations Guide

## Normal operation

1. Accept an approved Operations Planner reference and existing workflow, automation, and runtime references.
2. Create a bounded pipeline whose steps target only approved integration modules.
3. Run all six validations.
4. Queue and dispatch through the existing scheduler and worker adapter.
5. Observe stages, monitoring, results, and metrics.
6. Archive completed executions according to local retention policy.

Pause immediately when a restriction, unresolved challenge, risk denial, unhealthy runtime, or workspace mismatch is reported. Never retry a platform restriction as a transient failure.

## Recovery

Recovery requires a checkpoint and re-runs validation before dispatch. Rollback reverses successful declared actions, releases resources, clears the queue and worker assignment, cleans the runtime, and writes an audit entry.

## API and dashboard

Read-only operational resources are available at:

- `/tiktok/execution/plans`
- `/tiktok/execution/pipelines`
- `/tiktok/execution/stages`
- `/tiktok/execution/checkpoints`
- `/tiktok/execution/results`
- `/tiktok/execution/monitoring`
- `/tiktok/execution/analytics`

The dashboard is `/tiktok-ai-execution-engine`.

## Windows local guide

Use the existing local runtime PowerShell scripts; no additional service is introduced. Start TKAI with `scripts\start-tkai.ps1`, open the loopback dashboard, and inspect execution health before admitting plans. Stop with `scripts\stop-tkai.ps1`. Keep reference-vault material outside logs and source control.
