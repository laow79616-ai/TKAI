# Local Configuration

Copy `configuration/local.example.json` to the ignored `configuration/local.json`. Supported modes are `development` and `production-local`. Hosts must remain loopback; defaults are API 8000, Dashboard 4173, and AI Studio 4174. `TKAI_<FIELD>` environment variables override non-path fields. Keep secret values in an external provider referenced by `secret_reference`.
