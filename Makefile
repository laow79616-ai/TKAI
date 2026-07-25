.PHONY: dev-up dev-down dev-logs dev-reset observability-up observability-down observability-status observability-logs

dev-up:
	docker compose up --build

dev-down:
	docker compose down

dev-logs:
	docker compose logs -f

dev-reset:
	docker compose down -v --remove-orphans

OBSERVABILITY_COMPOSE = docker compose -f docker-compose.yml -f docker-compose.observability.yml

observability-up:
	$(OBSERVABILITY_COMPOSE) up --build -d

observability-down:
	$(OBSERVABILITY_COMPOSE) down

observability-status:
	$(OBSERVABILITY_COMPOSE) ps

observability-logs:
	$(OBSERVABILITY_COMPOSE) logs -f prometheus grafana loki alloy alertmanager postgres-exporter nginx-exporter
