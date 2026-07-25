.PHONY: dev-up dev-down dev-logs dev-reset

dev-up:
	docker compose --profile development up --build

dev-down:
	docker compose --profile development down

dev-logs:
	docker compose --profile development logs -f

dev-reset:
	docker compose --profile development down -v --remove-orphans
