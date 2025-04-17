GRAFANA=docker compose -f docker/grafana-compose.yml
COMPOSE=docker compose -f docker/docker-compose.yml
CONSUMER=docker compose -f docker/consumer-compose.yml
NETWORK_NAME=coinbase-network

# Environment setup
.PHONY: venv
venv:
	python -m venv .venv
	@echo "Run 'source .venv/bin/activate' (Linux/Mac) or '.venv\\Scripts\\activate' (Windows)"

.PHONY: install
install:
	pip install -r requirements.txt

# Network management
.PHONY: network-create
network-create:
	@if [ -z "$$(docker network ls -q -f name=${NETWORK_NAME})" ]; then \
		docker network create ${NETWORK_NAME}; \
		echo "Network ${NETWORK_NAME} created"; \
	else \
		echo "Network ${NETWORK_NAME} already exists"; \
	fi

.PHONY: network-remove
network-remove:
	@if [ -n "$$(docker network ls -q -f name=${NETWORK_NAME})" ]; then \
		docker network rm ${NETWORK_NAME}; \
		echo "Network ${NETWORK_NAME} removed"; \
	else \
		echo "Network ${NETWORK_NAME} does not exist"; \
	fi

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
.PHONY: infra-up
infra-up: network-create
	${COMPOSE} up -d

.PHONY: infra-down
infra-down:
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
up-all: infra-up grafana-up

.PHONY: down-all
down-all: infra-down grafana-down

# Cleanup
.PHONY: clean
clean: down-all
	@echo "Stopped all services"

.PHONY: kill
kill: clean network-remove
	docker volume prune -f 