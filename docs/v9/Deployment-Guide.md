# V9 Deployment Guide

TKAI V9 uses the existing container and local-runtime deployment models.
Prerequisites are Python 3.10+, Node.js 18+ for frontend builds, and the same
datastores and environment variables as V8. Never package `.env`, credentials,
cookies, sessions, caches, virtual environments, or `node_modules`.

Deploy the verified archives, validate SHA-256 hashes, start services with the
existing deployment tooling, then verify liveness, readiness, compatibility
health, dashboards, AI Studio, and OpenAPI. Roll back by redeploying the prior
release through established operations; V9 exposes no rollback endpoint.
