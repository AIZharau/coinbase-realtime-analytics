GRAFANA=docker compose -f docker/grafana-compose.yml
COMPOSE=docker compose -f docker/docker-compose.yml
CONSUMER=docker compose -f docker/consumer-compose.yml
PRODUCER=docker compose -f docker/producer-compose.yml
AIRFLOW=docker compose -f docker/airflow/docker-compose.yaml
NETWORK_NAME=coinbase-network
LOCAL_BIN = .local/bin
TF_VERSION=1.5.7
YC_VERSION=latest

# Environment setup
.PHONY: venv
venv:
	python3 -m venv .venv
	@echo "Run 'source .venv/bin/activate' (Linux/Mac) or '.venv\\Scripts\\activate' (Windows)"

.PHONY: install
install:
	pip install -r requirements.txt

.PHONY: install-yc
install-yc:
	@echo "Installing YC CLI to $(LOCAL_BIN)..."
	@mkdir -p $(LOCAL_BIN)
	@curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | \
		bash -s -- --install-dir $(LOCAL_BIN) --no-add-to-path
	@mv nstall-dir/* .local
	@rm -rf nstall-dir
	@echo "Run: export PATH=\"$$PWD/$(LOCAL_BIN):\$$PATH\""


.PHONY: install-terraform
install-terraform:
	@echo "Installing Terraform ${TF_VERSION} to ${LOCAL_BIN}..."
	@mkdir -p ${LOCAL_BIN}
	@wget https://hashicorp-releases.yandexcloud.net/terraform/${TF_VERSION}/terraform_${TF_VERSION}_darwin_arm64.zip -O ${LOCAL_BIN}/terraform.zip
	@unzip -o ${LOCAL_BIN}/terraform.zip -d ${LOCAL_BIN}
	@rm -f ${LOCAL_BIN}/terraform.zip
	@chmod +x ${LOCAL_BIN}/terraform
	@echo "Terraform installed. Add to PATH: export PATH=\"$$PWD/${LOCAL_BIN}:\$$PATH\""
	@${LOCAL_BIN}/terraform version

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

.PHONY: produce-docker-up
produce-docker-up:
	${PRODUCER} up --build -d producer

.PHONY: produce-docker-down
produce-docker-down:
	${PRODUCER} down producer

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

# Airflow operations
.PHONY: airflow-setup
airflow-setup:
	mkdir -p orchestration/{dags,plugins,logs}
	@echo "Created Airflow directories"

.PHONY: airflow-build
airflow-build:
	${AIRFLOW} build --no-cache

.PHONY: airflow-up
airflow-up:
	${AIRFLOW} up -d

.PHONY: airflow-down
airflow-down:
	${AIRFLOW} down

.PHONY: airflow-logs
airflow-logs:
	${AIRFLOW} logs -f airflow-standalone

# Database operations
.PHONY: init-db
init-db:
	curl http://localhost:8123 --data-binary @queries/clickhouse_tables.sql

# Terraform operations
.PHONY: tf-init
tf-init:
	@PATH="$(shell pwd)/$(LOCAL_BIN):$$PATH" terraform -chdir=terraform init

.PHONY: tf-plan
tf-plan:
	@PATH="$(shell pwd)/$(LOCAL_BIN):$$PATH" terraform -chdir=terraform plan

.PHONY: tf-apply
tf-apply:
	@PATH="$(shell pwd)/$(LOCAL_BIN):$$PATH" terraform -chdir=terraform apply -auto-approve

.PHONY: tf-destroy
tf-destroy:
	@PATH="$(shell pwd)/$(LOCAL_BIN):$$PATH" terraform -chdir=terraform destroy -auto-approve

.PHONY: tf-output
tf-output:
	@PATH="$(shell pwd)/$(LOCAL_BIN):$$PATH" terraform -chdir=terraform output

.PHONY: yc-init
yc-init:
	@PATH="$(shell pwd)/$(LOCAL_BIN):$$PATH" yc init

.PHONY: infra-cloud-up
infra-cloud-up: tf-init tf-apply
	@echo "Cloud infrastructure deployed"

.PHONY: infra-cloud-down
infra-cloud-down: tf-destroy
	@echo "Cloud infrastructure destroyed"

# Utility commands
.PHONY: up-all
up-all: infra-up grafana-up

.PHONY: pipeline-up
pipeline-up: infra-up consume-docker-up produce-docker-up grafana-up
	@echo "Full pipeline started"

.PHONY: pipeline-down
pipeline-down: consume-docker-down produce-docker-down
	@echo "Pipeline services stopped"

.PHONY: orchestration-up
orchestration-up: pipeline-up airflow-up
	@echo "Full pipeline with orchestration started"

.PHONY: orchestration-down
orchestration-down: pipeline-down airflow-down
	@echo "Pipeline with orchestration stopped"

.PHONY: down-all
down-all: infra-down grafana-down pipeline-down airflow-down

# Cleanup
.PHONY: clean
clean: down-all
	@echo "Stopped all services"

.PHONY: kill
kill: clean network-remove
	docker volume prune -f 