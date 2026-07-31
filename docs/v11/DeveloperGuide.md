# TKAI V11 Developer Guide

V11 is implemented under `src/tkai/v11`. Extend the immutable `Component` registry
with pure projection methods only. Public advisory APIs must be deterministic GET
operations. Never add runtime, scheduler, workflow, deployment, browser, migration,
upgrade, rollback, or TikTok-account execution behavior.

Run `python -m pytest tests/v11` and the production verifier before release.
