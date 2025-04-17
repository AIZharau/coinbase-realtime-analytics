# PROJECT SETUP GUIDE

## 1. Prerequisites
- Docker and Docker Compose installed
- Python 3.9+
- Make utility
- curl (for database initialization)

## 2. Initial Setup

### Create Python environment:
```bash
make venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
make install
```

## 3. Start Infrastructure Services

### Option A: Start all services at once:
```bash
make up-all
```

### Option B: Start services individually:
```bash
# Build network
make network-create

# Start Redpanda (Kafka-compatible message broker)
make redpanda-up

# Start Grafana and ClickHouse
make grafana-up
```

## 4. Initialize Database
```bash
make init-db
```

## 5. Run Data Pipeline

You can run components both locally and in containers:

### Option 1: Run the entire pipeline in containers
```bash
make pipeline-up
```

### Option 2: Launch components separately

**Run Producer:**
```bash
# Local
make produce

# In Docker container
make produce-docker-up
```

**Run Consumer:**
```bash
# Local
make consume

# In Docker container
make consume-docker-up
```

## 6. Access Monitoring Interfaces

| Service            | URL                      | Credentials       |
|--------------------|--------------------------|-------------------|
| Grafana Dashboard  | http://localhost:3000    | admin/admin       |
| Redpanda Console   | http://localhost:8080    | -                 |
| ClickHouse HTTP    | http://localhost:8123    | -                 |

## 7. Management Commands

### Service Control:
```bash
# Stop all services
make down-all

make pipeline-down

# Stopping individual components
make redpanda-down
make grafana-down
make produce-docker-down
make consume-docker-down
```

### Maintenance:
```bash
# Rebuild Grafana containers
make grafana-build

# Clean up everything
make clean

# Release all resources
make kill
```

## 8. Cloud Deployment (Yandex Cloud)

For production environments, you can deploy the infrastructure to Yandex Cloud using Terraform.

### Prerequisites:
- Terraform installed (version >= 1.0.0)
- Yandex Cloud CLI installed and configured
- Service account with appropriate permissions
- SSH key pair for VM access

### Cloud Architecture:

The cloud infrastructure includes:
- A virtual machine running Redpanda, Producer, and Consumer as systemd services
- A managed ClickHouse cluster for data storage
- S3-compatible object storage for raw data

The components work together as follows:
1. The Producer service on the VM connects to the Coinbase WebSocket feed
2. Data is streamed to a Redpanda instance running on the same VM
3. The Consumer service reads from Redpanda and loads data into the managed ClickHouse service
4. Grafana can connect to the ClickHouse service to visualize the data

### Deployment Steps:

1. **Configure Yandex Cloud Credentials**:
```bash
# Configure environment variables
cp terraform/.env.template terraform/.env
# Edit the file with your credentials
source terraform/.env
```

2. **Deploy Infrastructure**:
```bash
# Initialize and apply Terraform configuration
make infra-cloud-up
```

3. **Verify Deployment**:
```bash
# View outputs (clickhouse host, VM IP, etc.)
make tf-output
```

4. **Access the VM**:
```bash
# SSH into the virtual machine
ssh ubuntu@<vm_external_ip>
```

5. **Destroy Resources**:
```bash
# When finished, tear down the infrastructure
make infra-cloud-down
```

For more details, see the [Terraform README](../terraform/README.md).

## Troubleshooting

1. **Port conflicts**:
   - Check running containers: `docker ps`
   - Stop conflicting services

2. **Consumer issues**:
   - Verify Redpanda is running: `make logs`
   - Check database connection

3. **Grafana dashboard not loading**:
   - Wait 30-60 seconds after startup
   - Check logs: `make grafana-logs`

4. **Docker issues**:
   - Ensure Docker daemon is running
   - Check available resources (`docker stats`)

## Development Tips

- To modify the consumer logic, edit `src/main/clickhouse_consumer.py`
- Producer configuration is in `src/main/coinbase_producer.py`
- Database schema is defined in `queries/clickhouse_tables.sql`
- Use `make clean` before committing to ensure no containers are running