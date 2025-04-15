GRAFANA=docker compose -f docker/grafana-compose.yml
COMPOSE=docker compose -f docker/docker-compose.yml
CONSUMER=docker compose -f docker/consumer-compose.yml

# Environment setup
.PHONY: venv
venv:
	python -m venv .venv
	@echo "Run 'source .venv/bin/activate' (Linux/Mac) or '.venv\\Scripts\\activate' (Windows)"

.PHONY: install
install:
	pip install -r requirements.txt

# Data pipeline
.PHONY: produce
produce:
	python3 src/main/coinbase_producer.py

.PHONY: consume
consume:
	python3 src/main/clickhouse_consumer.py

.PHONY: consume-docker-up
consume-docker-up:
	${CONSUMER} up --build -d consumer

.PHONY: consume-docker-down
consume-docker-down:
	${CONSUMER} down consumer

# Infrastructure
.PHONY: redpanda-up
redpanda-up:
	${COMPOSE} up -d

.PHONY: redpanda-down
redpanda-down:
	${COMPOSE} down

.PHONY: grafana-build
grafana-build:
	${GRAFANA} build --no-cache

.PHONY: grafana-up
grafana-up:
	${GRAFANA} up -d

.PHONY: grafana-down
grafana-down:
	${GRAFANA} down

# Database operations
.PHONY: init-db
init-db:
	curl http://localhost:8123 --data-binary @queries/clickhouse_tables.sql

# Utility commands
.PHONY: up-all
up-all: redpanda-up grafana-up

.PHONY: down-all
down-all: redpanda-down grafana-down

.PHONY: logs
logs:
	${COMPOSE} logs -f

.PHONY: grafana-logs
grafana-logs:
	${GRAFANA} logs -f

# Cleanup
.PHONY: clean
clean: down-all
	@echo "Stopped all services"