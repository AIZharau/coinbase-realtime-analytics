# Real-Time Cryptocurrency Analytics Pipeline

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/) 
[![Redpanda](https://img.shields.io/badge/Streaming-Redpanda-ff69b4)](https://redpanda.com/)
[![Docs](https://img.shields.io/badge/Docs-API%20Reference-blueviolet)](docs/api_reference.md)

## Documentation Quick Links
- [🛠️ Quick Start Guide](docs/quick_start.md) - Get running in 5 minutes
- [📚 API Reference](docs/api_reference.md) - Producer/consumer interfaces
- [📊 Dashboard Samples](dashboards/) - Grafana examples

## Current Architecture
![Pipeline Diagram](https://github.com/AIZharau/coinbase-realtime-analytics/blob/main/docs/images/pipeline.png)  
*Current architecture overview*

Lightweight pipeline for processing Coinbase market data with clear upgrade paths.

## Getting Started

1. Initial Setup
Follow the [Quick Start Guide](docs/quick_start.md) Guide for:
- Environment preparation
- Service configuration
- First-run verification

2. Key Operations
```bash
# Start core services (see 
docker/README.md)
make pipeline-up

# OR launching core services without Producer/Consumer
make infra-up
```

3. Cloud Deployment (Yandex Cloud)
```bash
# Deploy infrastructure to Yandex Cloud
make infra-cloud-up

# View infrastructure outputs
make tf-output

# Destroy cloud infrastructure
make infra-cloud-down
```

4. Monitoring
Access pre-built dashboards:
![Grafana Sample](dashboards/dash.png)

## Project Structure

```
.
├── docker/                # Container configurations
│   ├── redpanda/          # (Future) WASM transform configs
│   ├── producer/          # Coinbase producer container
│   ├── consumer/          # ClickHouse consumer container
│   ├── grafana/           # Dashboard provisioning
│   └── *.yml             # Compose files
├── src/main/
│   ├── coinbase_producer.py # WebSocket client
│   ├── clickhouse_consumer.py # Data loader
│   └── utils/            # Shared helpers
├── terraform/            # Infrastructure as code
│   ├── *.tf              # Terraform configuration files
│   └── README.md         # Terraform setup instructions
├── docs/                 # Technical documentation
│   ├── api_reference.md  # Interface specifications
│   ├── quick_start.md    # Setup instructions
│   └── pipeline.png      # Architecture diagram
├── dashboards/           # Grafana JSON exports
└── Makefile              # Common tasks
```

## Roadmap

### Near-term
✓ JSON messaging  
✓ Docker deployment  
✓ Basic Grafana dashboards  
✓ Containerized Producer/Consumer

### Planned
◉ WASM transformations in Redpanda  
◉ Avro schema enforcement  
✓ Terraform infrastructure  
◉ Workflow orchestration  


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