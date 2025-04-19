# Real-Time Cryptocurrency Analytics Pipeline

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/) 
[![Redpanda](https://img.shields.io/badge/Streaming-Redpanda-ff69b4)](https://redpanda.com/)
[![Airflow](https://img.shields.io/badge/Orchestration-Airflow-017CEE)](https://airflow.apache.org/)
[![ClickHouse](https://img.shields.io/badge/Database-ClickHouse-FFCC01)](https://clickhouse.com/)
[![Docs](https://img.shields.io/badge/Docs-API%20Reference-blueviolet)](docs/api_reference.md)

## Documentation Quick Links
- [📚 Documentation Index](docs/index.md) - Complete documentation directory
- [🛠️ Quick Start Guide](docs/quick_start.md) - Get running in 5 minutes
- [📊 Dashboard Samples](dashboards/) - Grafana examples
- [🔄 Workflow Orchestration](docker/airflow/README.md) - Airflow setup and DAGs
- [☁️ Cloud Deployment](terraform/README.md) - Terraform infrastructure

## Current Architecture
Lightweight pipeline for processing Coinbase market data with clear upgrade paths and workflow orchestration.
![Pipeline Diagram](https://github.com/AIZharau/coinbase-realtime-analytics/blob/main/docs/images/pipeline.png)  

[Full architecture overview](docs/architecture.md) 

## Getting Started

1. **Initial Setup**
   Follow the [Quick Start Guide](docs/quick_start.md) for:
   - Environment preparation
   - Service configuration
   - First-run verification

2. **Key Operations**
   ```bash
   # Start core services
   make pipeline-up

   # OR with workflow orchestration
   make orchestration-up

   # Install CLI tools for cloud deployment
   make install-terraform
   make install-yc
   
   # Deploy to cloud
   make infra-cloud-up
   ```

3. **Component Access**
   - Grafana: http://localhost:3000 (admin/admin)
   - Airflow: http://localhost:8081 (airflow/airflow)
   - ClickHouse: http://localhost:8123/play
   - Redpanda Console: http://localhost:8080

## Common Commands

| Command | Description |
|---------|-------------|
| `make pipeline-up` | Start the full pipeline |
| `make orchestration-up` | Start pipeline with Airflow |
| `make down-all` | Stop all services |
| `make infra-cloud-up` | Deploy to cloud |
| `make infra-cloud-down` | Destroy cloud infrastructure |

For a complete list of commands, see the [Makefile Commands Reference](docs/quick_start.md#common-makefile-commands).

## Project Structure

```
.
├── docker/                # Container configurations
│   ├── redpanda/          # (Future) WASM transform configs
│   ├── producer/          # Coinbase producer container
│   ├── consumer/          # ClickHouse consumer container
│   ├── grafana/           # Dashboard provisioning
│   ├── airflow/           # Airflow configuration
│   └── *.yml              # Compose files
├── src/main/
│   ├── coinbase_producer.py # WebSocket client
│   ├── clickhouse_consumer.py # Data loader
│   └── utils/            # Shared helpers
├── orchestration/        # Airflow workflows
│   ├── dags/             # DAG definitions
│   ├── plugins/          # Airflow plugins
│   └── logs/             # Airflow logs
├── terraform/            # Infrastructure as code
│   ├── *.tf              # Terraform configuration files
│   └── README.md         # Terraform setup instructions
├── docs/                 # Technical documentation
│   ├── index.md          # Documentation index
│   ├── api_reference.md  # Interface specifications
│   ├── quick_start.md    # Setup instructions
│   └── architecture.md   # Architecture documentation
├── dashboards/           # Grafana JSON exports
└── Makefile              # Common tasks
```

## Orchestration Workflows

The project includes automated workflows using Apache Airflow:

1. **Market Data ETL** - Daily aggregation and analysis of trading data
2. **Infrastructure Management** - Weekly infrastructure verification and updates
3. **System Monitoring** - Hourly health checks of all system components

Access to the Airflow UI: http://localhost:8081

## Roadmap

### Near-term
✓ JSON messaging  
✓ Docker deployment  
✓ Basic Grafana dashboards  
✓ Containerized Producer/Consumer  
✓ Workflow orchestration  

### Planned
◉ WASM transformations in Redpanda  
◉ Avro schema enforcement  
✓ Terraform infrastructure  
◉ Advanced analytics pipelines  


## Performance

| Metric          | Current | Target |
|----------------|---------|--------|
| Latency        | 800ms   | 300ms  |
| Throughput     | 10K/s   | 50K/s  |
| Availability   | 99.5%   | 99.95% |

## Contribution

1. Fork the repository
2. Create feature branch (`git checkout -b feature`)
3. Commit changes (`git commit -am 'Add feature'`)
4. Push to branch (`git push origin feature`)
5. Open Pull Request