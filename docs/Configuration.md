# TKAI V5.0 Local Configuration

Copy `configuration/local.example.json` to `configuration/local.json`.
Configuration is typed and validated by `LocalRuntimeConfig`; environment
overrides use `TKAI_<FIELD_NAME>`.

The API, Dashboard, and AI Studio default to loopback on ports 8000, 4173, and
4174. Ports must be unique and in the range 1024–65535. Runtime and database
paths must remain inside the repository. Plaintext database credentials are
rejected; secrets use an external provider reference.

Default limits bound browsers, tabs, workflows, publishing, collection,
interaction, queues, payloads, exports, and query rows. Increase a limit only
after measuring local CPU and memory. Logs, PID references, SQLite data, browser
profiles, media, exports, backups, and temporary files stay below `runtime/`.
