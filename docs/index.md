# Coinbase Realtime Analytics Documentation

Welcome to the documentation for the Coinbase Realtime Analytics project. This index provides links to all available documentation resources.

## Core Documentation

| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | System architecture, components, and data flow |
| [Quick Start Guide](quick_start.md) | Getting started with local development |
| [API Reference](api_reference.md) | API interfaces and protocols |

## Component Documentation

| Component | Documentation |
|-----------|---------------|
| [Airflow](../docker/airflow/README.md) | Workflow orchestration configuration and DAGs |
| [Terraform](../terraform/README.md) | Infrastructure as code for cloud deployment |

## Workflows and Processes

| Workflow | Description |
|----------|-------------|
| [Market Data ETL](../orchestration/dags/market_data_etl.py) | Data processing pipeline for market data |
| [Infrastructure Management](../orchestration/dags/infrastructure_management.py) | Infrastructure provisioning and management |
| [System Monitoring](../orchestration/dags/system_monitoring.py) | Health and performance monitoring |

## Development Resources

| Resource | Description |
|----------|-------------|
| [Makefile Commands](quick_start.md#common-makefile-commands) | Available commands for development |
| [Deployment Models](architecture.md#deployment-models) | Local and cloud deployment options |
| [Contribution Guidelines](../README.MD#contribution) | How to contribute to the project |

## Additional Resources

- [Terraform Documentation](https://developer.hashicorp.com/terraform/docs)
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [ClickHouse Documentation](https://clickhouse.com/docs)
- [Redpanda Documentation](https://docs.redpanda.com/) 