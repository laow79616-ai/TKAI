.PHONY: dev-up dev-down dev-logs dev-reset

dev-up:
	docker compose up --build

dev-down:
	docker compose down

dev-logs:
	docker compose logs -f

dev-reset:
	docker compose down -v --remove-orphans
