# Enterprise Architecture Guide

TKAI 12.0.0 is the stable baseline. Product surfaces are the Python framework, HTTP service, dashboard, AI Studio, deployment definitions, and release/verification assets.

Productization MUST preserve runtime behavior, TikTok integrations, public APIs, and OpenAPI semantics. Identity, authorization, audit, tenancy, secrets, observability, backup, recovery, and capacity are explicit enterprise boundaries. Distributions are traceable to one commit and verified with SHA-256. Component details remain in `docs/architecture`, `docs/server`, `docs/deployment`, and `docs/v12`. Contract changes require separate authorization, compatibility review, migration guidance, and versioning.
