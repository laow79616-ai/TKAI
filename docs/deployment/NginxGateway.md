# Nginx Production Gateway

TKAI exposes one public entry point through Nginx. PostgreSQL, the API, and the
Dashboard have no host port mappings and are reachable only on the private
Docker Compose network.

## Development (HTTP)

Copy `.env.example` to `.env`, set the PostgreSQL credentials, and start the
default HTTP deployment:

```console
docker compose up --build
```

Open `http://localhost` (or the port selected with `HTTP_PORT`). The Dashboard
uses the same origin and sends API traffic through `/api`.

## Production (HTTPS)

Provide a PEM certificate and private key. Their host paths are configured with
`TLS_CERTIFICATE_PATH` and `TLS_PRIVATE_KEY_PATH`; the files are mounted
read-only and are never copied into an image.

```dotenv
HTTP_PORT=80
HTTPS_PORT=443
TLS_CERTIFICATE_PATH=/absolute/path/to/fullchain.pem
TLS_PRIVATE_KEY_PATH=/absolute/path/to/private-key.pem
```

Start the production deployment by merging the HTTPS override into the base
Compose file:

```console
docker compose -f docker-compose.yml -f docker-compose.production.yml up --build -d
```

The production gateway serves HTTPS and permanently redirects every public
HTTP request to its HTTPS equivalent. `/nginx-health` remains available over
the container's loopback HTTP listener for the Docker health check.

Both modes register the same `nginx` service. The override replaces its HTTP
configuration with the HTTPS configuration and adds the TLS certificate mounts
and public HTTPS port.

## Routing

Nginx strips the `/api/` prefix before proxying API requests. It also proxies
`/docs`, `/openapi.json`, `/health`, `/ready`, `/live`, and `/metrics` to the
API. `/ready` and `/live` map to the API's `/health/ready` and `/health/live`
routes. Every other request goes to the Dashboard.

Responses use gzip where appropriate, browser security headers, and one-year
immutable caching for fingerprinted static asset extensions. Production adds
HSTS. The gateway forwards the original host, client address, and protocol.

## Certificate rotation

Replace the certificate files atomically at their configured host paths, then
validate and reload Nginx:

```console
docker compose -f docker-compose.yml -f docker-compose.production.yml exec nginx nginx -t
docker compose -f docker-compose.yml -f docker-compose.production.yml exec nginx nginx -s reload
```

Do not commit certificates, keys, or `.env`. Restrict private-key permissions
to the deployment operator.

## Validation and troubleshooting

Validate the complete model without starting containers:

```console
docker compose config --quiet
docker compose config --services
docker compose -f docker-compose.yml -f docker-compose.production.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.production.yml config --services
```

Both service-list commands must print `postgres`, `api`, `dashboard`, and
`nginx`.

Inspect `docker compose ps` and Nginx logs when a health check fails. A
gateway that is healthy while public routes return `502` usually indicates
that the API or Dashboard is unavailable; inspect their health and logs next.
