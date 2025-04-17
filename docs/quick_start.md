# Quick Start Guide

This guide will help you set up and run the Coinbase Realtime Analytics pipeline on your local machine.

## Prerequisites

- Docker and Docker Compose
- Python 3.9 or higher
- Git
- 4GB RAM minimum (8GB recommended)
- For cloud deployment:
  - [Terraform CLI](https://developer.hashicorp.com/terraform/install) (v1.0.0+)
  - [Yandex Cloud CLI](https://cloud.yandex.com/docs/cli/quickstart) (configured with valid credentials)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/coinbase-realtime-analytics.git
   cd coinbase-realtime-analytics
   ```

2. Set up virtual environment (optional):
   ```bash
   make venv
   source .venv/bin/activate  # On Linux/Mac
   # OR
   .venv\Scripts\activate     # On Windows
   ```

3. Install dependencies:
   ```bash
   make install
   ```

## Running the Pipeline

### Basic Setup

1. Start the infrastructure (ClickHouse, Redpanda):
   ```bash
   make infra-up
   ```

2. Initialize the database schema:
   ```bash
   make init-db
   ```

3. Start the dashboards:
   ```bash
   make grafana-up
   ```

4. Start the data pipeline:
   ```bash
   make produce-docker-up
   make consume-docker-up
   ```

5. Start everything at once (alternative):
   ```bash
   make pipeline-up
   ```

### Workflow Orchestration with Airflow

1. Set up and start Airflow:
   ```bash
   make airflow-up
   ```

2. Access the Airflow UI:
   - URL: http://localhost:8081
   - Username: `airflow`
   - Password: `airflow`

3. Start the complete system with orchestration:
   ```bash
   make orchestration-up
   ```

## Cloud Deployment with Terraform

1. Install required tools:
   ```bash
   # Install Terraform CLI (example for Ubuntu)
   make install-terraform
   
   # Install Yandex Cloud CLI
   make install-yc
   ```

2. Configure Yandex Cloud credentials:
   ```bash
   # Configure yc CLI
   yc init
   
   # Export required variables
   export YC_TOKEN=$(yc iam create-token)
   export YC_CLOUD_ID=$(yc config get cloud-id)
   export YC_FOLDER_ID=$(yc config get folder-id)
   ```

3. Deploy to the cloud:
   ```bash
   make infra-cloud-up
   ```

4. Get deployment information:
   ```bash
   make tf-output
   ```

5. Destroy cloud resources when done:
   ```bash
   make infra-cloud-down
   ```

For detailed information on Terraform infrastructure, refer to [Terraform Documentation](../terraform/README.md).

## Monitoring

1. Grafana dashboards are available at:
   - URL: http://localhost:3000
   - Username: `admin`
   - Password: `admin`

2. Redpanda Console is available at:
   - URL: http://localhost:8080

3. ClickHouse has a web interface at:
   - URL: http://localhost:8123/play

## Stopping the Pipeline

1. Stop individual components:
   ```bash
   make grafana-down
   make consume-docker-down
   make produce-docker-down
   make infra-down
   make airflow-down
   ```

2. Stop everything at once:
   ```bash
   make down-all
   ```

3. Clean up all resources (including volumes):
   ```bash
   make kill
   ```

## Common Makefile Commands

Below is a list of all available Makefile commands grouped by purpose:

### Setup
- `make venv` - Create Python virtual environment
- `make install` - Install project dependencies
- `make network-create` - Create Docker network
- `make install-terraform` - Install Terraform CLI
- `make install-yc` - Install Yandex Cloud CLI

### Pipeline
- `make pipeline-up` - Start full pipeline (infrastructure, producer, consumer, Grafana)
- `make pipeline-down` - Stop pipeline services
- `make orchestration-up` - Start pipeline with Airflow orchestration
- `make orchestration-down` - Stop pipeline with Airflow orchestration

### Individual Services
- `make infra-up` - Start base infrastructure (Redpanda, ClickHouse)
- `make grafana-up` - Start Grafana dashboards
- `make produce-docker-up` - Start Coinbase data producer
- `make consume-docker-up` - Start ClickHouse consumer
- `make airflow-up` - Start Airflow orchestration

### Cloud Operations
- `make tf-init` - Initialize Terraform
- `make tf-plan` - Plan Terraform changes
- `make tf-apply` - Apply Terraform changes
- `make tf-destroy` - Destroy Terraform resources
- `make infra-cloud-up` - Deploy to cloud
- `make infra-cloud-down` - Destroy cloud resources

### Cleanup
- `make down-all` - Stop all services
- `make clean` - Clean up local resources
- `make kill` - Remove all resources including volumes and networks

## Troubleshooting

1. Check component logs:
   ```bash
   docker logs redpanda
   docker logs clickhouse
   docker logs grafana
   make airflow-logs
   ```

2. Reset the environment:
   ```bash
   make kill
   make pipeline-up
   ```

## Next Steps

- Explore the [API Reference](api_reference.md) for integration details
- Review the [Airflow Workflows](../docker/airflow/README.md) for orchestration
- Check out the [Terraform Guide](../terraform/README.md) for cloud deployment
- Understand the [Architecture](architecture.md) of the system