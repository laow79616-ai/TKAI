# Enterprise TikTok Device Center

## Architecture

The Device Center is the local, single-user TKAI V5.0 control plane for approved
Android, iOS, emulator, simulator-reference, and virtual-device workflows. It
owns inventory, groups, versioned profiles, queues, reservations, health,
recovery, telemetry, and statistics. It does not own device drivers, TikTok
sessions, accounts, proxies, workflows, risk policy, audit infrastructure, or
observability infrastructure.

Narrow ports connect it to the existing Browser Cluster, Browser Runtime,
Account Center, Proxy Center, Workflow Center, Operations Center, and Risk
Control Center. Reference adapters are deterministic test doubles and never
contact a device or TikTok. Integrations exchange opaque references such as
`device://id`; secrets and raw credentials are not accepted.

## Lifecycle

The supported states are Discovered, Provisioning, Ready, Running, Busy, Paused,
Recovering, Offline, Archived, and Deleted. The service validates every
transition. Deleted is terminal, and only an archived device can be deleted.
Reservation sets a ready device to Busy; release returns it to Ready and may
apply a cooldown.

## Device types

Supported inventory types are Android, iPhone, Android Emulator, iOS Simulator
Reference, Virtual Device, and Future Extension. iOS simulators and virtual
devices are references to approved local runtimes. The module contains no
spoofing, platform-security bypass, restriction bypass, CAPTCHA bypass, or
anti-detection behavior.

## Profiles

Profiles include resolution, language, timezone, locale, region, device-profile
reference, and a monotonically increasing version. Resolution uses
`WIDTHxHEIGHT`. Profiles are workspace-scoped and validated before assignment.
A profile configures approved runtime behavior; it does not alter or falsify
hardware identity.

## Scheduling and allocation

The scheduler provides a device queue, priority ordering, workspace partitioning,
retry attempts, delayed availability, and a maximum concurrent-device bound.
Stable sequence ordering prevents priority ties from starving older work.
Allocation enforces global, workspace, and account-affinity limits. Reservations
have timeouts, explicit release, and cooldown. Expired reservations do not count
toward capacity.

## Health and failure detection

Heartbeat snapshots track connectivity, battery, CPU, memory, storage, and
runtime. Values are validated and converted into an explainable health score.
Connectivity loss or a score below 40 marks the device Offline and increments
the failure metric. Device adapters should report temperature only as a runtime
reference when the platform exposes it; no unsupported sensor access is implied.

## Recovery

Bounded recovery attempts reconnect, restart, reinitialize, and profile reload
in order, stopping after the first successful action. Policies enforce cooldown,
maximum attempts, and optional manual approval. Recovery stops immediately and
pauses the device when Risk Control reports an unresolved TikTok restriction or
challenge. Operators must resolve the platform condition and explicitly approve
further work; Device Center never bypasses it.

## Telemetry and statistics

Prometheus-style metrics are:

- `tiktok_devices_total`
- `tiktok_devices_ready`
- `tiktok_devices_running`
- `tiktok_devices_offline`
- `tiktok_device_health_score`
- `tiktok_device_recoveries`
- `tiktok_device_failures`
- `tiktok_device_cpu_usage`
- `tiktok_device_memory_usage`

Statistics expose available, busy, and offline devices; average runtime; failure
rate; recovery success; and utilization. Dashboard sections cover Overview,
Devices, Groups, Profiles, Queues, Resources, Health, Recovery, Telemetry, and
Statistics.

## API

Read-only dashboard bindings are available at:

- `/tiktok/device-center`
- `/tiktok/device-center/devices`
- `/tiktok/device-center/groups`
- `/tiktok/device-center/profiles`
- `/tiktok/device-center/health`
- `/tiktok/device-center/recovery`
- `/tiktok/device-center/statistics`

Callers provide tenant, workspace, and actor scope. Mutating service calls
require explicit `write`, `control`, `schedule`, or `recover` RBAC permission.

## Security

Every resource is tenant- and workspace-scoped. RBAC is enforced before access,
and mutations create actor-attributed audit entries. Serial numbers, accounts,
proxies, sessions, and credentials must be encrypted references managed by
existing services. Metadata keys containing password, secret, token, cookie,
credential, or session are removed. Queues, concurrent devices, workspace
reservations, account affinity, recovery attempts, timeouts, and cooldowns are
bounded. Logs and dashboard responses must never contain secrets.

## Operations guide

1. Register or discover a device through an approved local adapter.
2. Move it from Discovered to Provisioning, validate connectivity and profile,
   then move it to Ready.
3. Queue approved workflow demand with workspace, account reference, device
   type, priority, and optional delay.
4. Allocate a bounded reservation and pass only its device reference to existing
   workflow/runtime services.
5. Record periodic health snapshots and release reservations on completion.
6. Investigate Offline devices before recovery. If Risk Control reports a
   challenge or restriction, leave the device Paused for manual review.
7. Archive retired devices before deletion. Preserve audit and aggregate metrics
   according to the existing platform retention policy.

## Windows local guide

Use PowerShell from the repository root:

```powershell
python -m pytest tests\tiktok\test_device_center.py
python -m ruff check tiktok\device_center tests\tiktok\test_device_center.py
python -m mypy tiktok\device_center
npm --prefix dashboard\frontend run build
npm --prefix studio\frontend run build
```

Device discovery remains disabled unless an approved local adapter is explicitly
configured. Tests use mocks only and require neither live devices nor TikTok
access. Follow the existing local runtime start/stop guide for the API and
dashboard; do not expose the service beyond its configured local interface.
