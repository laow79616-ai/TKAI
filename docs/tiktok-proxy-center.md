# Enterprise TikTok Proxy Center

## Architecture

The Proxy Center is a TikTok-only control plane under `tiktok.proxy_center`. Its
domain service owns proxy inventory, groups, health records, verification
results, rotation policies, bindings, allocation state, scheduling, statistics,
audit entries, and Prometheus metrics. Framework-neutral HTTP registration keeps
the domain independent of FastAPI. The Browser Runtime consumes only the
secret-free `ProxyAllocationPort`; Account Center identifiers are opaque
references. Existing vault, authorization, audit, API gateway, event streaming,
observability, workflow, automation, Docker, Kubernetes, and CI/CD services are
not duplicated.

## Proxy lifecycle

The lifecycle is `Draft -> Available -> In Use -> Available/Cooling`.
Operators may disable available, in-use, or cooling proxies. Disabled proxies
may return to available, be archived, or be deleted. Expired proxies may only be
archived or deleted; archived proxies may only be deleted. Deletion is a soft,
terminal state. Active allocations must be released before administrative
retirement.

## Groups

Static and dynamic pools, residential, datacenter, mobile, country, project, and
account groups are tenant/workspace scoped. Static membership uses proxy IDs.
Dynamic filters contain classification data only and never credentials.

## Rotation

Policies support manual, interval, request-count, session, TikTok-account,
workspace, and failure-triggered rotation. Every rotation releases the old
allocation, chooses a health-aware replacement, increments
`tiktok_proxy_rotations_total`, and adds an audit/history record. Cooldown and
failure thresholds are bounded configuration.

## Health and verification

Health combines connectivity, latency, bandwidth reference, availability,
success/failure rates, consecutive failures, last check, and a normalized score.
Verification checks DNS, TCP, TLS when applicable, public IP, geo, protocol, and
credential-reference authentication. It never calls a TikTok endpoint. Production
public-IP/geo checking is supplied through `VerificationTransport`; tests use
local doubles.

## Bindings

Bindings address Browser Runtime, TikTok Account, workspace, project, or
automation workflow targets. Priority, affinity, and sticky-session references
guide allocation. A binding selects exactly one proxy or group. References are
opaque and do not copy account, browser, project, or workflow records.

## Pool and scheduler

Pool operations are acquire, release, reserve, recycle, and drain. Minimum and
maximum size, concurrency, queue depth, retry, and timeout bounds prevent
unbounded consumption. The priority queue applies target bindings, health score,
region/country preference, and least-used fairness. Failed selection is retried
with bounded backoff ordering; no network wait occurs in the scheduler.

## Security

Every resource is tenant/workspace scoped and every operation checks RBAC.
Credential material is stored only by the platform secret service; Proxy Center
retains `credential_reference`. Hosts cannot embed credentials, metadata is
secret-filtered, and audit records contain IDs only. Do not place resolver
results, usernames, passwords, tokens, cookies, or session values in logs.

Suggested permissions are `tiktok:proxy:read`, `write`, `verify`, `rotate`,
`bind`, `acquire`, `release`, and `admin`. Production secret resolvers must
enforce the same tenant and workspace boundary before resolving encrypted
material.

## Operations guide

1. Create or identify an encrypted credential in the platform vault.
2. Register a draft proxy using only its credential reference.
3. Verify it through a configured non-TikTok verification transport.
4. Move a successful proxy to available.
5. Create groups and target bindings, then monitor pool depth, health, latency,
   failures, queue depth, allocation history, and rotation history.
6. Disable or drain unhealthy capacity, observe cooldown, then recycle or
   archive it.

Alert on exhausted pool depth, sustained failure growth, low health score,
latency regression, or queue saturation. Preserve audit and allocation history
according to platform retention policy. Before upgrades, drain allocations and
run lifecycle, deployment, release, API, metrics, and frontend build tests.

## Windows local operations guide

From PowerShell at the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\tiktok\test_proxy_center.py
.\.venv\Scripts\ruff.exe check tiktok\proxy_center tests\tiktok\test_proxy_center.py
.\.venv\Scripts\mypy.exe tiktok\proxy_center
Push-Location dashboard\frontend
npm run build
Pop-Location
```

Use only mock/local verification adapters during development. Windows Firewall
may block local TCP test doubles; bind them to loopback and never weaken system
firewall policy. Secrets belong in the configured encrypted store, not
PowerShell history, environment dumps, `.env`, command arguments, or logs.

## API and metrics

The API root is `/tiktok/proxy-center` with `proxies`, `groups`, `health`,
`rotation`, `bindings`, `pool`, and `statistics` resources plus `dashboard` and
`metrics`. Metrics are:

- `tiktok_proxies_total`
- `tiktok_proxy_active_total`
- `tiktok_proxy_health_score`
- `tiktok_proxy_failures_total`
- `tiktok_proxy_rotations_total`
- `tiktok_proxy_pool_depth`
- `tiktok_proxy_latency_seconds`
