# TKAI Business Platform V2 Architecture

Version 2.0.0 extends the existing V6-V12 and Business Platform V1 composition. It
adds no framework layer. FastAPI hosts authenticated `/business/v2` management APIs;
SQLite stores tenant/workspace-scoped metadata, settings, and append-only audit rows;
the React Dashboard and AI Studio remain separate Vite applications.

All product records use `(tenant, workspace, id)` identity, timestamps, indexed
module/status lookup, transactional writes, and soft archive. Accounts, browsers,
proxies, tasks, content, reports, AI Studio assets, and administration objects share
the validated metadata contract. References may identify secrets, cookies, sessions,
proxies, user-data directories, or external execution services, but values are never
returned. This product does not launch browsers, switch proxies, publish, message,
execute workflows, or perform TikTok actions.
