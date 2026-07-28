# TikTok Data Collection Center Architecture

The Data Collection Center is a tenant- and workspace-isolated control plane for
configured collection projects, jobs, datasets, and analytics pipelines. It does
not contact TikTok directly. Account validation, browser collection, proxy
health, workflow checkpoints, and Automation schedules are bounded ports backed
by existing TKAI services. Tests use deterministic null adapters only.

The domain packages are `projects`, `jobs`, `sources`, `datasets`, `filters`,
`tasks`, `pipelines`, `storage`, `history`, `analytics`, `dashboard`, and `api`.
The service owns orchestration and audit state; encrypted objects remain in the
platform storage service and are represented only by `kms://` or `vault://`
references.

A project binds one configured source to one versioned dataset. A task executes
the ordered Collection, Validation, Transformation, Storage, and Analytics
pipeline. Workflow owns checkpoints and recovery references. Dashboard and API
surfaces expose scoped summaries, never credentials or raw secrets.

## Integrations

- Account Center validates scoped account references.
- Browser Runtime implements an authorized, configured collection adapter.
- Proxy Center reports route health without exposing proxy credentials.
- Workflow records pipeline checkpoints and recovery state.
- Automation registers scheduled and recurring tasks.
- Dashboard consumes `/tiktok/data/dashboard`.

No adapter implements unauthorized access, CAPTCHA bypass, restriction bypass,
or automated circumvention of TikTok protections.
