.PHONY: up down seed logs logs-api logs-frontend restart clean

COMPOSE := docker compose

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

seed:
	$(COMPOSE) run --rm api python /seed/seed.py

logs:
	$(COMPOSE) logs -f

logs-api:
	$(COMPOSE) logs -f api

logs-frontend:
	$(COMPOSE) logs -f frontend

restart:
	$(COMPOSE) restart api frontend

clean:
	$(COMPOSE) down -v
	docker system prune -f
