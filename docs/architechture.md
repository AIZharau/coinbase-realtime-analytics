# Architecture Real-Time Crypto Analytics

## System overview
![Architecture Diagram](https://github.com/AIZharau/coinbase-realtime-analytics/blob/main/docs/images/pipeline.png)

## Current Architecture

```mermaid
graph TD
    A[Coinbase WS] -->|JSON| B[Python Producer]
    B --> C[Redpanda]
    C --> D[ClickHouse Consumer]
    D --> E[ClickHouse Tables]
    E --> F[Grafana]
```

### Core Components
1. **Producer** (`coinbase_producer.py`)
   - Connects to Coinbase WebSocket
   - Streams JSON messages to Redpanda
   - Handles connection failures

2. **Consumer** (`clickhouse_consumer.py`)
   - Reads from Redpanda topics
   - Writes to ClickHouse tables
   - Basic data validation

3. **Storage**:
   - Create KafkaEngine table
   - Create MaterializedView
   - Create MergeTree tables

4. **Visualization**:
   - Pre-built Grafana dashboards
   - Real-time price tracking
   - Volume analytics
