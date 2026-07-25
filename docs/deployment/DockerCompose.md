# Docker Compose Development Deployment

## Scope

This is a local, three-service development deployment for Marketplace Server:
PostgreSQL, the FastAPI API, and the Dashboard. It does not introduce
Kubernetes, HTTPS, reverse proxies, queues, Redis, or cloud deployment.

## Requirements

- Docker Engine with Docker Compose v2
- An available local port `8000` for the API and `4173` for the Dashboard

## First Start

```text
cp .env.example .env
# Change POSTGRES_PASSWORD before use.
make dev-up
```

Compose starts PostgreSQL first, waits for its health check, then starts the
API. The API performs a bounded readiness probe (30 attempts by default) and
runs the packaged Alembic migration when `POSTGRES_MIGRATE=true`. The Dashboard
starts after the API health check passes.

The Dashboard receives `VITE_API_BASE_URL` at build time. Compose defaults it
to `http://localhost:${API_PORT}`; direct dashboard development still defaults
to `/api` when the variable is absent.

## Operations

```text
make dev-down       # stop containers and retain named PostgreSQL volume
make dev-logs       # follow service logs
make dev-reset      # stop containers and remove local database data
```

`dev-reset` is intentionally destructive only for the named local development
volume and requires an explicit operator command.

## Environment Variables

| Variable | Purpose |
| --- | --- |
| `POSTGRES_HOST`, `POSTGRES_PORT` | PostgreSQL service location |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Explicit database credentials |
| `API_HOST`, `API_PORT` | API bind address and exposed host/container port |
| `DASHBOARD_PORT` | Dashboard host port |
| `POSTGRES_MIGRATE` | Enables migration during API startup |
| `POSTGRES_WAIT_ATTEMPTS` | Bounded database connection attempts |
| `POSTGRES_WAIT_INTERVAL_SECONDS` | Delay between attempts |
| `VITE_API_BASE_URL` | Dashboard API URL, injected at image build time |

## Troubleshooting

- If the API does not become healthy, inspect `make dev-logs` and confirm the
  PostgreSQL credentials in `.env` match the named volume's initial setup.
- If a password is changed after first startup, run `make dev-reset` before
  restarting because PostgreSQL initializes credentials only for an empty data
  volume.
- Migration failures leave the API container stopped; correct configuration and
  restart it rather than relying on infinite retries.

## Known Limitations

- This compose file is for local development only.
- Foundation services retain their existing explicit storage injection; no API
  contract or Foundation behavior is modified by deployment configuration.
- No TLS, authentication provisioning, production secrets manager, backups,
  scaling, or high availability is included.
