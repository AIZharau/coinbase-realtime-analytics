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

Open two terminal windows:

**Terminal 1 (Producer):**
```bash
make produce
```

**Terminal 2 (Consumer):**
```bash
make consume
```

### Alternative: Run consumer in Docker
```bash
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

# Stop specific components
make redpanda-down
make grafana-down
make consume-docker-down
```

### Logs Monitoring:
```bash
# View Redpanda logs
make logs

# View Grafana logs
make grafana-logs
```

### Maintenance:
```bash
# Rebuild Grafana containers
make grafana-build

# Clean up everything
make clean
```

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