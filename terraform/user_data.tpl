#!/bin/bash

# Update packages
apt-get update
apt-get upgrade -y

# Install Docker and Docker Compose
apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Create directory structure
mkdir -p /opt/coinbase-analytics
cd /opt/coinbase-analytics

# Clone repository
apt-get install -y git
git clone https://github.com/AIZharau/coinbase-realtime-analytics.git .

# Create environment configuration for cloud services
cat > .env << EOF
CLICKHOUSE_HOST=${clickhouse_host}
CLICKHOUSE_USER=${clickhouse_user}
CLICKHOUSE_PASSWORD=${clickhouse_password}
REDPANDA_BROKERS=localhost:9092
EOF

# Ensure directory structure exists
mkdir -p docker/redpanda

# Create custom docker-compose for standalone Redpanda
cat > docker/redpanda-compose.yml << EOF
version: "3.7"

services:
  redpanda:
    image: redpandadata/redpanda:v24.2.18
    restart: on-failure
    container_name: redpanda
    hostname: redpanda
    ports:
      - "9092:9092"
      - "8080:8080"
    volumes:
      - redpanda-data:/var/lib/redpanda/data
    command:
      - redpanda
      - start
      - --kafka-addr PLAINTEXT://0.0.0.0:9092
      - --advertise-kafka-addr PLAINTEXT://localhost:9092
      - --rpc-addr 0.0.0.0:33145
      - --advertise-rpc-addr localhost:33145
      - --smp 1
      - --memory 1G
      - --mode dev-container
      - --default-log-level=warn
    networks:
      - coinbase-network

  redpanda-console:
    image: docker.redpanda.com/redpandadata/console:v2.3.1
    container_name: redpanda-console
    ports:
      - "8080:8080"
    depends_on:
      - redpanda
    command: "/app/console"
    environment:
      KAFKA_BROKERS: "redpanda:9092"
    networks:
      - coinbase-network

networks:
  coinbase-network:
    name: coinbase-network

volumes:
  redpanda-data:
EOF

# Update producer and consumer configuration to use environment variables
# First check if configuration file exists
if [ -f "src/main/utils/config.py" ]; then
    # Use pattern matching that's safer for variable substitution
    sed -i "s|'bootstrap.servers': os.getenv('REDPANDA_BROKERS', '.*')|'bootstrap.servers': os.getenv('REDPANDA_BROKERS', 'localhost:9092')|" src/main/utils/config.py
    sed -i "s|'host': os.getenv('CLICKHOUSE_HOST', '.*')|'host': os.getenv('CLICKHOUSE_HOST', '${clickhouse_host}')|" src/main/utils/config.py
    sed -i "s|'user': os.getenv('CLICKHOUSE_USER', '.*')|'user': os.getenv('CLICKHOUSE_USER', '${clickhouse_user}')|" src/main/utils/config.py
    sed -i "s|'password': os.getenv('CLICKHOUSE_PASSWORD', '.*')|'password': os.getenv('CLICKHOUSE_PASSWORD', '${clickhouse_password}')|" src/main/utils/config.py
else
    echo "WARNING: Configuration file not found at src/main/utils/config.py"
fi

# Create a systemd service for the Redpanda
cat > /etc/systemd/system/redpanda.service << EOF
[Unit]
Description=Redpanda Service
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/coinbase-analytics
ExecStart=/usr/bin/docker compose -f docker/redpanda-compose.yml up
ExecStop=/usr/bin/docker compose -f docker/redpanda-compose.yml down
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Create a systemd service for the producer
cat > /etc/systemd/system/coinbase-producer.service << EOF
[Unit]
Description=Coinbase Producer Service
After=redpanda.service
Requires=redpanda.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/coinbase-analytics
ExecStart=/usr/bin/python3 src/main/coinbase_producer.py
Restart=always
Environment="REDPANDA_BROKERS=localhost:9092"

[Install]
WantedBy=multi-user.target
EOF

# Create a systemd service for the consumer
cat > /etc/systemd/system/coinbase-consumer.service << EOF
[Unit]
Description=Coinbase Consumer Service
After=redpanda.service
Requires=redpanda.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/coinbase-analytics
ExecStart=/usr/bin/python3 src/main/clickhouse_consumer.py
Restart=always
Environment="REDPANDA_BROKERS=localhost:9092"
Environment="CLICKHOUSE_HOST=${clickhouse_host}"
Environment="CLICKHOUSE_USER=${clickhouse_user}"
Environment="CLICKHOUSE_PASSWORD=${clickhouse_password}"

[Install]
WantedBy=multi-user.target
EOF

# Create network
docker network create coinbase-network

# Install Python requirements
apt-get install -y python3-pip
pip3 install -r requirements.txt

# Initialize ClickHouse database schema
cat > init_clickhouse.sql << EOF
CREATE database IF NOT EXISTS coinbase_market_data;

CREATE TABLE IF NOT EXISTS coinbase_market_data.raw_trades (
    type String,
    sequence Int64,
    product_id String,
    price Float64,
    open_24h Float64,
    volume_24h Float64,
    low_24h Float64,
    high_24h Float64,
    volume_30d Float64,
    best_bid Float64,
    best_bid_size Float64,
    best_ask Float64,
    best_ask_size Float64,
    side Nullable(String),
    time DateTime64(3),
    trade_id Int64,
    last_size Float64
) ENGINE = MergeTree()
ORDER BY (product_id, time);

CREATE TABLE IF NOT EXISTS coinbase_market_data.ohlc (
    product_id String,
    time DateTime,
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume Float64
) ENGINE = MergeTree()
ORDER BY (product_id, time);

CREATE TABLE IF NOT EXISTS coinbase_market_data.spreads (
    product_id String,
    time DateTime,
    spread Float64,
    bid Float64,
    ask Float64,
    bid_size Float64,
    ask_size Float64
) ENGINE = MergeTree()
ORDER BY (product_id, time);

CREATE TABLE IF NOT EXISTS coinbase_market_data.anomalies (
    product_id String,
    time DateTime,
    price_jump Float64,
    volume_spike Float64,
    current_price Float64,
    last_price Float64,
    current_volume Float64,
    last_volume Float64,
    details String
) ENGINE = MergeTree()
ORDER BY (product_id, time);
EOF

# Install curl and initialize database
apt-get install -y curl
curl -X POST "http://${clickhouse_host}:8123" --data-binary @init_clickhouse.sql -u ${clickhouse_user}:${clickhouse_password}

# Install and configure Grafana
apt-get install -y apt-transport-https software-properties-common
wget -q -O - https://packages.grafana.com/gpg.key | apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | tee -a /etc/apt/sources.list.d/grafana.list
apt-get update
apt-get install -y grafana

# Create Grafana datasource for ClickHouse
mkdir -p /etc/grafana/provisioning/datasources/
cat > /etc/grafana/provisioning/datasources/clickhouse.yaml << EOF
apiVersion: 1
datasources:
  - name: ClickHouse
    type: vertamedia-clickhouse-datasource
    url: http://${clickhouse_host}:8123
    access: proxy
    basicAuth: false
    jsonData:
      defaultDatabase: "coinbase_market_data"
      username: "${clickhouse_user}"
      usePost: true
      addCorsHeader: true
      tlsSkipVerify: true
      timeout: 30
    secureJsonData:
      password: "${clickhouse_password}"
    editable: true
EOF

# Enable and start Grafana
systemctl enable grafana-server
systemctl start grafana-server

# Enable and start services
systemctl daemon-reload
systemctl enable redpanda.service
systemctl enable coinbase-producer.service
systemctl enable coinbase-consumer.service
systemctl start redpanda.service
# Wait for Redpanda to start
sleep 30
systemctl start coinbase-producer.service
systemctl start coinbase-consumer.service

echo "Coinbase analytics pipeline setup completed!" 