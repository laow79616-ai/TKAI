# Testing Guide

Run `python scripts/validate-enterprise.py`. It covers Ruff, mypy, pytest, Vulture, imports, dependencies, packages, archives, security/secrets, dashboard, AI Studio, and OpenAPI. Tests must be deterministic, isolated, and free of real credentials or uncontrolled network calls. Fixes add regression tests where practical. Skipped, flaky, or environment-blocked gates are blockers.
