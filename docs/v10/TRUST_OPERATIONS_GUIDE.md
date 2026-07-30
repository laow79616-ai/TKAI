# Trust Mesh Operations Guide

Use GET endpoints under `/v10/trust` to inspect profiles, domains, identities,
relationships, integrity, attestations, scores, compatibility, health, and
metrics. There are no write endpoints or operational commands.

Release validation covers Ruff, configured mypy, focused and regression tests,
TikTok/deployment/release/local-runtime suites, frontend builds, OpenAPI,
operational scripts under `scripts/`, and `git diff --check`. Tests use mocks.
