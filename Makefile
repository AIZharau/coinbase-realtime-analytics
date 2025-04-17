GRAFANA=docker compose -f docker/grafana-compose.yml
COMPOSE=docker compose -f docker/docker-compose.yml
CONSUMER=docker compose -f docker/consumer-compose.yml
PRODUCER=docker compose -f docker/producer-compose.yml
AIRFLOW=docker compose -f docker/airflow/docker-compose.yaml
NETWORK_NAME=coinbase-network
TF_VERSION=1.6.5
YC_VERSION=latest

# Environment setup
.PHONY: venv
venv:
	python -m venv .venv
	@echo "Run 'source .venv/bin/activate' (Linux/Mac) or '.venv\\Scripts\\activate' (Windows)"

.PHONY: install
install:
	pip install -r requirements.txt

.PHONY: install-terraform
install-terraform:
	@echo "Installing Terraform ${TF_VERSION}..."
	@if [ -f /etc/os-release ]; then \
		. /etc/os-release; \
		case "$$ID" in \
			ubuntu|debian) \
				sudo apt-get update && sudo apt-get install -y gnupg software-properties-common curl; \
				curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -; \
				sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $$(lsb_release -cs) main"; \
				sudo apt-get update && sudo apt-get install -y terraform=${TF_VERSION}; \
				echo "Terraform installed successfully." ;; \
			centos|rhel|fedora) \
				sudo yum install -y yum-utils; \
				sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo; \
				sudo yum -y install terraform-${TF_VERSION}; \
				echo "Terraform installed successfully." ;; \
			*) \
				echo "Unsupported OS. Please install Terraform manually from https://developer.hashicorp.com/terraform/install" ;; \
		esac \
	else \
		echo "Cannot detect OS. Please install Terraform manually from https://developer.hashicorp.com/terraform/install"; \
	fi
	@echo "Verifying Terraform installation..."
	@terraform version

.PHONY: install-yc
install-yc:
	@echo "Installing Yandex Cloud CLI..."
	@if [ -f /etc/os-release ]; then \
		. /etc/os-release; \
		case "$$ID" in \
			ubuntu|debian) \
				curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash; \
				echo "Yandex Cloud CLI installed successfully." ;; \
			centos|rhel|fedora) \
				curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash; \
				echo "Yandex Cloud CLI installed successfully." ;; \
			*) \
				echo "Unsupported OS. Please install Yandex Cloud CLI manually from https://cloud.yandex.com/docs/cli/quickstart" ;; \
		esac \
	else \
		echo "Cannot detect OS. Please install Yandex Cloud CLI manually from https://cloud.yandex.com/docs/cli/quickstart"; \
	fi
	@echo "Verifying Yandex Cloud CLI installation..."
	@yc version || echo "Please restart your shell or run 'source ~/.bashrc' to use yc command"

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
	cd terraform && terraform init

.PHONY: tf-plan
tf-plan:
	cd terraform && terraform plan

.PHONY: tf-apply
tf-apply:
	cd terraform && terraform apply

.PHONY: tf-destroy
tf-destroy:
	cd terraform && terraform destroy

.PHONY: tf-output
tf-output:
	cd terraform && terraform output

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