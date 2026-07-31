# TKAI Business Platform V1.0

TKAI Business Platform is the V12 product layer for tenant-scoped TikTok business metadata. It composes existing TKAI account, browser, proxy, content, analytics, AI, and enterprise capabilities without changing framework contracts.

The Business API is mounted at `/business/v1`. It is GET-only and advisory. It cannot launch browsers, switch proxies, execute tasks, send messages, upload or publish content. Existing V6 through V12 routes remain unchanged.

## Product modules

- Account Center: inventory, import/export references, cookies, sessions, browser/device/proxy references, tags, groups, lifecycle, health, search, filtering, and batch metadata.
- Browser Center: Chromium, Playwright, user-data directory, inventory, and health references.
- Proxy Center: HTTP, HTTPS, SOCKS5, provider, region, availability, health, and rotation policy references.
- Task Center: Like, Follow, Favorite, Comment, Browse, Search, Message, Upload, and Collection templates, groups, history, and audit metadata.
- Content Center: drafts, videos, images, captions, hashtags, schedules, and library metadata.
- Data Center: statistics, KPIs, reports, charts, trends, dashboards, and export metadata.
- AI Studio: prompt, skill, agent, workflow, knowledge, model, memory, and validation centers.
- Enterprise Admin: organizations, teams, users, roles, permissions, audit, settings, and policies.

