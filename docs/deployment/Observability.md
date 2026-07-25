# TKAI observability stack

Sprint-3 adds an optional operations stack without changing the four-service
default deployment. Prometheus, Grafana, Loki, Grafana Alloy, Alertmanager,
PostgreSQL exporter, and Nginx exporter are enabled only through
`docker-compose.observability.yml`.

## Configure and start

Copy `.env.example` to `.env` and replace `GRAFANA_ADMIN_USER`,
`GRAFANA_ADMIN_PASSWORD`, and the PostgreSQL password. No real credentials
belong in version control. Retention defaults to 15 days for Prometheus and
168 hours for Loki.

Linux or macOS:

```sh
docker compose -f docker-compose.yml -f docker-compose.observability.yml up --build -d
make observability-status
make observability-logs
make observability-down
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
docker compose -f docker-compose.yml -f docker-compose.observability.yml up --build -d
docker compose -f docker-compose.yml -f docker-compose.observability.yml ps
docker compose -f docker-compose.yml -f docker-compose.observability.yml logs -f prometheus grafana loki alloy alertmanager postgres-exporter nginx-exporter
docker compose -f docker-compose.yml -f docker-compose.observability.yml down
```

For HTTPS production, insert the production override before observability:

```powershell
docker compose -f docker-compose.yml -f docker-compose.production.yml -f docker-compose.observability.yml up --build -d
```

Grafana is at `http://127.0.0.1:3000`, Prometheus at port 9090, Loki at
3100, and Alertmanager at 9093. Exporters use ports 9187 and 9113. Every
published monitoring port binds to `127.0.0.1`; the monitoring network is
internal.

## Metrics, dashboards, alerts, and logs

Prometheus scrapes the API `/metrics`, PostgreSQL exporter, Nginx exporter,
and itself. Alerts cover API, PostgreSQL, and Nginx availability, any down
target, and elevated 5xx ratio. The API currently exposes request and
status-code counters but no request-duration histogram. Consequently the
overview dashboard explicitly marks API latency unavailable, and there is no
latency alert. This avoids fabricating unsupported queries.

The provisioned TKAI Overview dashboard shows service and target availability,
request rate, 5xx ratio, PostgreSQL health, Nginx health, and service logs.
Alloy reads Docker logs only for the API, Nginx, PostgreSQL, and Dashboard.
Labels contain service/container identity only; environment values and
credentials are not copied into labels.

Alertmanager uses a local receiver by default. Operators can add an approved
notification receiver in their private deployment configuration.

## Operational notes

Alloy requires read-only access to the Docker socket. Treat access to Grafana
and the host as privileged. Named volumes preserve data across restarts; use
`docker compose ... down -v` only when intentionally deleting monitoring data.
The Nginx exporter reads the restricted `/nginx-status` endpoint from the
Docker network; that endpoint is denied to public clients.
