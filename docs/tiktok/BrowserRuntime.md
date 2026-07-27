# TikTok Browser Runtime

## Architecture

The browser runtime is the tenant- and workspace-scoped execution foundation for
TikTok Account Center and future TikTok automation. The domain service owns
lifecycle, contexts, pages, encrypted storage, queueing, pooling, health, and
recovery. Browser processes and Account Center updates are bounded ports. The
default `ReferenceBrowserDriver` is deterministic and launches no executable;
Playwright, Chromium, Chrome-channel, and Edge-channel adapters are opt-in.

The runtime makes no anti-detection, stealth, CAPTCHA bypass, security bypass, or
restriction-circumvention guarantee.

## Browser lifecycle

Instances use Draft, Provisioning, Ready, Running, Idle, Paused, Recovering,
Failed, Stopped, Archived, and Deleted states. Launch, pause, resume, release,
stop, drain, recovery, manual stop, and the kill switch are audited. Pool,
account, workspace, tab, queue, lifetime, idle, and navigation bounds are
validated before work begins.

## Profiles and fingerprint configuration

Profiles bind an account to directory references, user agent, timezone, locale,
languages, viewport, screen, scale, color scheme, geolocation reference,
permissions, and download reference. Directory references reject traversal and
absolute paths outside the configured root. Fingerprint configuration is a
consistency-validated policy interface for canvas, WebGL, audio, fonts,
hardware, platform, touch, and media devices.

## Contexts and pages

Contexts can be created, launched, paused, resumed, closed, recycled, and
restored. Persistent contexts use encrypted storage references; ephemeral
contexts remain isolated. Pages support bounded tab creation, close, HTTP(S)
navigation, reload, back, forward, wait-for-load, health, active-page state, and
screenshot references.

## Storage and account integration

Cookies, LocalStorage, SessionStorage, and IndexedDB references are represented
inside an authenticated encrypted storage-state object. Plaintext cookies and
sessions are never retained. TikTok-domain session validation detects login
pages, logged-in state, and expiry and updates Account Center through a narrow
tenant/workspace-scoped port. Repeated unrecoverable failures invoke the
account auto-pause port.

## Proxy binding

HTTP, HTTPS, and SOCKS5 bindings contain only username and password secret
references plus region, country, health, and sticky-session references. Runtime
logs and audit metadata remove credential-, cookie-, session-, secret-, and
token-shaped fields. Rotation is implemented by replacing the instance proxy
reference through an authorized control-plane adapter.

## Pool and scheduling

Pool configuration includes minimum, maximum, warm/idle/active counts,
per-account and per-workspace limits, acquire, release, recycle, and drain.
The priority launch queue provides account affinity, cancellation, timeouts,
concurrency limits, and a fixed backpressure ceiling.

## Health and recovery

Health snapshots track process, context, page, TikTok reachability, login,
proxy-reference health, memory, CPU reference, and heartbeat. Recovery covers
browser, context, page, and session restoration with bounded attempts and
exponential backoff. Exhaustion records the reason and requests Account Center
auto-pause.

## Security

Every operation validates RBAC plus tenant and workspace ownership. Storage
state is authenticated and encrypted, proxy credentials are secret references,
profile paths are constrained, resource usage is bounded, secrets are filtered
from metadata, and control actions are audited. Operators must use the kill
switch or manual stop when continued execution is unsafe.

## API and dashboard

The API is rooted at `/tiktok/browser-runtime` and exposes instances, profiles,
contexts, pages, storage, pool, queue, health, recovery, dashboard, and metrics.
The dashboard reports instances, profiles, account bindings, pool, queue,
health, sessions, storage, recovery, failures, and statistics.

## Operations guide

Use the reference driver for development and CI. Inject a production browser
adapter only after validating its executable/channel availability and secret
provider. Monitor queue depth, launch failures, crashes, recoveries, memory,
login health, and proxy health. Drain a workspace before maintenance. Enable the
kill switch during incidents, then inspect audit and recovery records before
resuming.

## Windows local operations

Windows development requires no installed browser by default. Run tests with
`.venv\Scripts\python.exe -m pytest tests\tiktok\test_browser_runtime.py`.
For an opt-in headed adapter, configure an approved Playwright browser/channel
outside this package, keep the profile root under a dedicated restricted
directory, and use secret references rather than environment values in
profiles. Never commit browser profiles, cookies, storage-state exports, proxy
credentials, screenshots containing private data, or downloaded account data.
