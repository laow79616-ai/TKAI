# ADR 001: Persistent Configuration Finalization

Status: Accepted

TKAI resolves configuration in the order Memory → Environment → Workspace →
User → Default when expressed as precedence; implementation merges low-to-high
to produce the same result. This keeps temporary runtime overrides explicit,
project settings portable, user settings local, and defaults deterministic.

Configuration and Credential Discovery remain decoupled. Configuration may
provide non-secret defaults, while credentials retain their independent runtime,
environment, dotenv, and static priority. We rejected a shared secret-bearing
configuration store because it would blur ownership and increase accidental
secret disclosure risk.
